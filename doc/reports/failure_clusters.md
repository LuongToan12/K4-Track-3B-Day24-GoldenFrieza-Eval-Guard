# Phân tích lỗi Phase A

Nhóm: GoldenFrieza

Người phụ trách: Lương Khánh Toàn - 2A202602836

Nguồn: `artifacts/ragas_50q.json`; run timestamp: 2026-10-12T10:20:01.778777+00:00.
Generation mode/fallback và điều kiện chạy: Chạy live 100% với `generation_mode="llm"` trên cả 50/50 câu hỏi (0 câu rơi vào `extractive_fallback`). Pipeline sử dụng chunking 500 ký tự (overlap 80), làm giàu ngữ cảnh với tiền tố `[Nguồn tài liệu: {source}]`, hybrid search BM25 + Dense (`BAAI/bge-m3`) trên Qdrant in-memory (`top_k=20`), và CrossEncoder reranker `BAAI/bge-reranker-v2-m3` lấy `top_k=3` chunks đưa vào LLM. Hai tệp PDF scan ảnh không có text layer (`BCTC.pdf`, `Nghi_dinh_so_13-2023_ve_bao_ve_du_lieu_ca_nhan_508ee.pdf`) được bỏ qua khi lập chỉ mục (tổng cộng 107 chunks từ các tài liệu chính sách Markdown).
Models generation/evaluator: generation=`["gpt-4o-mini-2024-07-18"]`; evaluator=`["gpt-4o-mini", "text-embedding-3-small"]`.

## Điểm theo distribution

| Metric | factual (20) | multi_hop (20) | adversarial (10) |
|---|---|---|---|
| faithfulness | 1.0000 (1.0) | 0.5690 (0.569048) | 0.7667 (0.766667) |
| answer_relevancy | 0.4957 (0.495686) | 0.4003 (0.400322) | 0.4427 (0.442727) |
| context_precision | 0.9667 (0.966667) | 0.9417 (0.941667) | 0.9833 (0.983333) |
| context_recall | 0.8750 (0.875000) | 0.8208 (0.820833) | 0.6833 (0.683333) |
| avg_score | 0.8343 (0.834338) | 0.6830 (0.682967) | 0.7190 (0.719015) |

Tính trên toàn bộ 50 câu hỏi, điểm trung bình toàn cục đạt **0.7507**, trong đó `factual` dẫn đầu (0.8343), tiếp theo là `adversarial` (0.7190), và thấp nhất là `multi_hop` (0.6830).

## Bottom 10 và nguyên nhân

Bảng dưới đây trích xuất chính xác 10 câu có `avg_score` thấp nhất từ `bottom_10` trong `artifacts/ragas_50q.json`:

| Rank | ID | Distribution | Question | avg_score | worst_metric | diagnosis | suggested_fix |
|---|---|---|---|---|---|---|---|
| 1 | 33 | multi_hop | Nhân viên Manager có thâm niên 12 năm: tổng phụ cấp hàng tháng và số ngày phép năm theo v2024 là bao nhiêu? | 0.3750 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 2 | 42 | adversarial | Thâm niên bao nhiêu năm thì được cộng thêm ngày phép? | 0.4167 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 3 | 50 | adversarial | Nhân viên Manager có thể dùng VPN cá nhân (như NordVPN) khi WFH để tăng bảo mật thêm không? | 0.4167 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 4 | 39 | multi_hop | So sánh yêu cầu mật khẩu giữa policy v1.0 và v2.0 về độ dài tối thiểu, thời hạn đổi và MFA. | 0.5299 | context_precision | Too many irrelevant chunks | Add reranking or metadata filter |
| 5 | 22 | multi_hop | Nếu cần mua một chiếc laptop 30 triệu cho nhân viên mới, ai phê duyệt và cần gì từ phòng CNTT? | 0.5417 | answer_relevancy | Answer doesn't match question | Improve prompt template |
| 6 | 24 | multi_hop | Nhân viên tạm ứng 15 triệu, sau 20 ngày mới thanh toán. Bị phạt bao nhiêu? | 0.5711 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 7 | 6 | factual | Thông tin lương thuộc cấp độ phân loại dữ liệu nào? | 0.5833 | answer_relevancy | Answer doesn't match question | Improve prompt template |
| 8 | 27 | multi_hop | Nhân viên có thâm niên 7 năm theo v2024 được nghỉ bao nhiêu ngày phép? Nếu bị trừ thêm 4 ngày ốm không có giấy y tế thì còn lại bao nhiêu? | 0.6164 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 9 | 38 | multi_hop | Nhân viên đi công tác nước ngoài 4 ngày tại thành phố lớn, ở khách sạn 200 USD/đêm (3 đêm). Công ty thanh toán bao nhiêu tiền khách sạn? | 0.6216 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 10 | 21 | multi_hop | Một nhân viên Senior có 9 năm thâm niên được nghỉ bao nhiêu ngày phép năm và lương trong khoảng nào? | 0.6250 | answer_relevancy | Answer doesn't match question | Improve prompt template |

**Đối chiếu chi tiết `answer` / `contexts` / `ground_truth` theo 4 nhóm nguyên nhân gốc rễ:**

1. **Lỗi Retrieval thiếu tài liệu thứ hai trong câu hỏi Multi-hop (ID 33, ID 21, ID 22):**
   - **Bằng chứng cụ thể:**
     - Ở **ID 33** (`avg_score = 0.3750`), câu hỏi yêu cầu cả *tổng phụ cấp hàng tháng của Manager* (`phu_cap.md`) và *số ngày phép năm theo v2024* (`nghi_phep_nam_v2024.md`). Tuy nhiên, cả 3/3 `contexts` sau rerank đều chỉ thuộc `nghi_phep_nam_v2024.md`, hoàn toàn vắng bóng `phu_cap.md` (`context_recall = 0.5`). Do thiếu thông tin phụ cấp và prompt hệ thống yêu cầu nói `"Không tìm thấy."` nếu thông tin không có trong context, LLM đã trả lời cụt lủn `"Không tìm thấy."`, kéo cả `faithfulness = 0.0` và `answer_relevancy = 0.0`.
     - Ở **ID 21** (`avg_score = 0.6250`), 3 chunks truy hồi gồm `nghi_phep_nam_v2024.md`, `nghi_phep_nam_v2023.md` và `nghi_phep_khong_luong.md`, thiếu hoàn toàn `bang_luong_2024.md`. Câu trả lời nêu đúng *"18 ngày phép năm (15 + 3)"* nhưng phải ghi nhận *"Về lương, không tìm thấy thông tin cụ thể trong các tài liệu đã cho"*, làm `answer_relevancy = 0.0` và `context_recall = 0.5`.
     - Ở **ID 22** (`avg_score = 0.5417`), chunk chứa bảng phân quyền phê duyệt đơn hàng 5–50 triệu của `mua_sam.md` bị đẩy khỏi top-3 bởi chunk `hoan_chi_dao_tao.md` (cũng có con số "30.000.000 VNĐ"), khiến LLM trả lời đúng yêu cầu CNTT nhưng báo *"Ai phê duyệt không được đề cập trong context"*.
2. **Lỗi Generation quá bảo thủ (`"Không tìm thấy."`) trước bẫy mâu thuẫn phiên bản hoặc câu hỏi gài giả định (ID 42, ID 50):**
   - **Bằng chứng cụ thể:**
     - Ở **ID 42** (`avg_score = 0.4167`), `contexts` chứa đồng thời cả `nghi_phep_nam_v2023.md` (*"từ 5 năm trở lên được cộng thêm 1 ngày phép"*) ở vị trí số 1 và `nghi_phep_nam_v2024.md` (*"Chính sách này thay thế hoàn toàn phiên bản 1.0... từ 3 năm trở lên được cộng thêm 1 ngày phép"*) ở vị trí số 2. Khi câu hỏi không nêu rõ năm ("Thâm niên bao nhiêu năm thì được cộng thêm ngày phép?"), LLM lúng túng trước hai con số mâu thuẫn (5 năm vs 3 năm) và trả lời `"Không tìm thấy."` thay vì ưu tiên bản v2024 hiện hành như `ground_truth`.
     - Ở **ID 50** (`avg_score = 0.4167`), `contexts[0]` (`vpn_truy_cap.md`) đã ghi rõ *"Không sử dụng VPN cá nhân (NordVPN, ExpressVPN) trong mạng công ty"*, nhưng câu hỏi gài thêm cụm *"nhân viên Manager... khi WFH để tăng bảo mật thêm"*. Vì context không nhắc riêng ngoại lệ cho cấp "Manager" hay mục đích "tăng bảo mật thêm", prompt bảo thủ khiến LLM trả lời `"Không tìm thấy."` thay vì khẳng định **"KHÔNG được phép"**.
3. **Lỗi Ragas Faithfulness phạt các bước diễn giải tính toán số học trung gian (ID 24, ID 27, ID 38):**
   - **Bằng chứng cụ thể:**
     - Ở **ID 24** (`avg_score = 0.5711`), LLM trả lời **đúng hoàn toàn kết quả 50.000 đồng** khớp với `ground_truth` (`2% × 15.000.000 × (5/30) = 50.000 VNĐ`), và `context_precision = 1.0`, `context_recall = 1.0`. Tuy nhiên, vì câu trả lời trình bày các bước biến đổi số học trung gian (`0.02 × 2,500,000 = 50,000`) không xuất hiện nguyên văn từng chữ trong văn bản quy chế `tam_ung.md`, bộ chấm `faithfulness` của Ragas đánh giá các mệnh đề số học suy diễn là không trích dẫn trực tiếp từ context (`faithfulness = 0.0`).
     - Tương tự, ở **ID 27** (`avg_score = 0.6164`, kết quả tính ra đúng **17 ngày** và **13 ngày còn lại**) và **ID 38** (`avg_score = 0.6216`, kết quả tính ra đúng **600 USD** cho 3 đêm × 200 USD), câu trả lời hoàn toàn chính xác về mặt nghiệp vụ nhưng bị Ragas chấm `faithfulness = 0.0` (ở ID 27, LLM còn giải thích nhầm lời dẫn *"từ năm thứ 6 trở đi"* dù phép cộng `15 + 2 = 17` đúng).
4. **Lỗi Chunking cắt ngang bảng/mục so sánh đa phiên bản (ID 39, ID 6):**
   - **Bằng chứng cụ thể:** Ở **ID 39** (`avg_score = 0.5299`), `mat_khau_v2.md` bị chia thành 3 chunks rời nhau; top-3 chỉ lấy được 2 chunks của `mat_khau_v2.md` (chứa MFA và chu kỳ 120 ngày, nhưng mất chunk đầu chứa yêu cầu *"tối thiểu 12 ký tự"*) và 1 chunk đầu của `mat_khau_v1.md` (chứa *"8 ký tự"*, nhưng mất chunk sau chứa chu kỳ *"90 ngày"*). Kết quả là `context_recall = 0.5` và LLM suy luận sai rằng v2.0 không quy định độ dài tối thiểu. Ở **ID 6** (`avg_score = 0.5833`), bảng 4 cấp độ phân loại trong `phan_loai_du_lieu.md` bị cắt sau dòng Cấp độ 1 (Công khai), làm mất dòng Cấp độ 3 (Bí mật - mã hóa khi truyền, need-to-know) nên câu trả lời chỉ nêu ngắn gọn *"Thông tin lương thuộc cấp độ Bí mật"* (`context_recall = 0.5`).

## Matrix và nhóm yếu nhất

Ma trận phân bố `worst_metric` (4 metrics × 3 distributions) trên toàn bộ 50 câu hỏi (mỗi câu hỏi được đếm đúng 1 lần vào metric thấp điểm nhất của câu đó):

| Metric \ Distribution | factual (20) | multi_hop (20) | adversarial (10) | Tổng số câu (50) |
|---|---|---|---|---|
| faithfulness | 0 | 8 | 2 | 10 |
| answer_relevancy | 18 | 11 | 7 | 36 |
| context_precision | 0 | 1 | 0 | 1 |
| context_recall | 2 | 0 | 1 | 3 |

Nhóm yếu theo mean thấp nhất: `multi_hop`; mean: `0.6830` (`0.682967374461994`).
Worst metric xuất hiện nhiều nhất: `answer_relevancy`; số câu: `36`.

**Giải thích nguyên nhân nhóm `multi_hop` có điểm trung bình thấp nhất (0.6830):**
- Không chọn theo tổng số câu (vì `factual` và `multi_hop` đều có 20 câu, còn `adversarial` có 10 câu), mà xét theo **điểm trung bình cộng 4 metrics (`avg_score`)**, `multi_hop` thấp nhất (`0.6830` so với `0.7190` của `adversarial` và `0.8343` của `factual`).
- Nguyên nhân cốt lõi gồm 2 tầng cộng hưởng:
  1. **Tầng Retrieval (`top_k=3` không đảm bảo độ phủ đa tài liệu):** Các câu hỏi `multi_hop` đòi hỏi ghép thông tin từ 2 tài liệu độc lập (ví dụ `nghi_phep_nam_v2024.md` + `bang_luong_2024.md` ở câu 21, hoặc `nghi_phep_nam_v2024.md` + `phu_cap.md` ở câu 33). Khi một tài liệu có nhiều chunks khớp từ khóa (như 3 chunks của `nghi_phep_nam_v2024.md`), reranker `top_k=3` lấp đầy cả 3 vị trí bằng cùng một tài liệu đó và đánh rơi tài liệu thứ hai, làm `context_recall` giảm xuống 0.8208.
  2. **Tầng Generation & Phép tính suy luận (`faithfulness = 0.5690`):** Nhiều câu `multi_hop` yêu cầu tính toán số học (tính lương thử việc 85% ở câu 25, 35; tính phạt quá hạn tạm ứng pro-rata ở câu 24, 29; tính chi phí khách sạn ở câu 31, 38). Khi LLM viết ra phép nhân/chia trung gian hoặc khi thiếu 1 trong 2 vế nên trả lời `"Không tìm thấy."` (câu 33), điểm `faithfulness` của `multi_hop` tụt mạnh xuống `0.5690` (so với `1.0000` của `factual`).
- **Vì sao `answer_relevancy` là `worst_metric` ở 36/50 câu:** Trên các câu `factual` mà `faithfulness = 1.0`, `context_precision ≈ 1.0` và `context_recall = 1.0`, chỉ số `answer_relevancy` của Ragas (đo độ tương đồng cosine giữa câu hỏi sinh ngược bằng tiếng Anh/Việt từ câu trả lời với câu hỏi gốc) luôn dao động quanh `0.40–0.75` do câu trả lời ngắn gọn trực diện (ví dụ `"Phụ cấp ăn trưa hàng tháng là 1.000.000 VNĐ."` ở câu 3 đạt `answer_relevancy = 0.4096` dù đúng 100%). Vì 3 chỉ số kia đạt tuyệt đối `1.0`, `answer_relevancy` tự động trở thành `min(METRICS)` của câu đó dù câu trả lời không hề sai.

**Đề xuất hướng khắc phục cụ thể và quy trình kiểm chứng lại:**
1. **Đa dạng hóa nguồn tài liệu khi Rerank (Per-source Diversity / MMR ở `src/m3_rerank.py`) và tăng `RERANK_TOP_K` lên 5:** Giới hạn tối đa 2 chunks từ cùng một file nguồn trong top-K để câu hỏi `multi_hop` luôn lấy được ít nhất 2 tài liệu khác nhau (khắc phục trực tiếp câu 21, 22, 33).
2. **Tăng `CHUNK_SIZE` từ 500 lên 800 ký tự theo ranh giới Markdown heading (`##`) ở `src/m1_chunking.py`:** Giữ trọn vẹn các bảng thẩm quyền phê duyệt (`mua_sam.md` câu 5, 22) và bảng phân loại dữ liệu (`phan_loai_du_lieu.md` câu 6) cũng như các mục trong `mat_khau_v2.md` (câu 39).
3. **Cập nhật System Prompt trong `scripts/setup_answers.py`:**
   - Yêu cầu LLM ưu tiên tài liệu có **Phiên bản / Ngày hiệu lực mới nhất (v2024, v2.0)** khi context chứa cả bản cũ lẫn bản mới (khắc phục câu 42).
   - Yêu cầu LLM trả lời bằng **câu hoàn chỉnh lặp lại chủ ngữ của câu hỏi** và trích dẫn rõ công thức gốc từ tài liệu trước khi ghi kết quả tính toán (cải thiện cả `answer_relevancy` lẫn `faithfulness` cho câu 24, 27, 38).
4. **Cách chạy lại để kiểm chứng:** Chạy lại `python scripts/setup_answers.py --live` và `python scripts/run_experiments.py --phase a --live`, sau đó so sánh `per_distribution.multi_hop.avg_score` (kỳ vọng tăng từ `0.6830` lên `≥ 0.78`) và kiểm tra xem các câu ID 21, 22, 33, 42, 50 có thoát khỏi `bottom_10` hay không.

## Bẫy adversarial và giới hạn

- **So sánh nhóm `adversarial` (10 câu, `avg_score = 0.7190`) với `factual` (`0.8343`) và `multi_hop` (`0.6830`):**
  - Nhóm `adversarial` có `context_precision` rất cao (`0.9833`) vì các câu hỏi ngắn và trúng đích từ khóa chính sách, nhưng `context_recall` thấp nhất trong 3 nhóm (`0.6833`) vì `ground_truth` của bộ test `adversarial` luôn chứa thêm các câu giải thích meta-context (ví dụ: *"Đây là negation trap — câu trả lời đúng là phủ định"* ở câu 46, 48 hoặc *"RAG có thể retrieve cả 2 tài liệu — câu trả lời đúng phải ưu tiên v2024"* ở câu 41, 43). Những câu chú thích meta này của người ra đề tất nhiên không tồn tại trong kho văn bản gốc nên Ragas chấm `context_recall = 0.6667` (2/3 câu trong ground_truth có mặt trong context).
  - Điều này chứng minh một bài học quan trọng: **Điểm Ragas thấp hơn trên tập `adversarial` (ví dụ `context_recall = 0.6833`) không tự chứng minh pipeline sập bẫy, và ngược lại điểm cao ở một metric cũng cần đọc kèm nội dung câu trả lời.**
- **Phân tích cụ thể kết quả xử lý bẫy Version Conflict và Negation Trap:**
  - **Các câu vượt bẫy thành công (8/10 câu):**
    - *Version conflict:* Câu **41** (trả lời đúng **15 ngày phép năm** theo v2024 bất chấp `nghi_phep_nam_v2023.md` nằm ngay ở `contexts[1]`), câu **43** (trả lời đúng **12 ký tự** theo v2.0), câu **44** (trả lời đúng **120 ngày** theo v2.0), câu **45** (trả lời đúng **bắt buộc kích hoạt MFA** theo v2.0), câu **49** (phân biệt đúng v2023 là 12 ngày và v2024 đang có hiệu lực). Việc `m5_enrichment.py` gắn tiền tố `[Nguồn tài liệu: ...]` cùng header phiên bản đã giúp `gpt-4o-mini` phân biệt tốt phiên bản ở 5/6 câu version conflict.
    - *Negation trap:* Câu **46** (trả lời đúng *"Nhân viên thử việc KHÔNG được nghỉ phép năm"*), câu **47** (trả lời đúng *"Không, nhân viên không nên tự xử lý malware"*), câu **48** (trả lời đúng *"Nhân viên thử việc chưa được hưởng gói bảo hiểm sức khỏe PVI"*).
  - **Hai câu thất bại nằm trong Bottom 10 (ID 42 và ID 50):**
    - **ID 42 (Version conflict — Rank 2 Bottom 10):** Khi `nghi_phep_nam_v2023.md` được xếp ở `contexts[0]` và `nghi_phep_nam_v2024.md` ở `contexts[1]`, LLM không tự quyết định chọn v2024 mà trả lời `"Không tìm thấy."`.
    - **ID 50 (Policy contradiction / Negation trap — Rank 3 Bottom 10):** Câu hỏi hỏi về *"Nhân viên Manager... dùng VPN cá nhân (như NordVPN) khi WFH để tăng bảo mật"*. Dù `contexts[0]` cấm mọi nhân viên dùng NordVPN, LLM lại trả lời `"Không tìm thấy."` vì không suy diễn quy tắc cấm chung sang trường hợp cụ thể "cấp Manager khi WFH".
- **Giới hạn của thực nghiệm Phase A:**
  - Bộ câu hỏi đánh giá có quy mô 50 câu (20 `factual`, 20 `multi_hop`, 10 `adversarial`), đủ để phát hiện cụm lỗi hệ thống nhưng khoảng tin cậy trên nhóm `adversarial` (`n = 10`) còn rộng (mỗi câu chiếm 10% trọng số nhóm).
  - Hai tài liệu PDF scan (`BCTC.pdf`, `Nghi_dinh_so_13-2023_ve_bao_ve_du_lieu_ca_nhan_508ee.pdf`) chưa được OCR trong bước lập chỉ mục.
  - Chỉ số `answer_relevancy` và `faithfulness` của Ragas phụ thuộc vào mô hình đánh giá `gpt-4o-mini` + `text-embedding-3-small`, nhạy cảm với độ dài câu trả lời và các bước diễn giải tính toán số học tiếng Việt.
