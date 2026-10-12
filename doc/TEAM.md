# Nhóm thực hiện K4 Track 3B

Tên nhóm: GoldenFrieza

Repo chung: https://github.com/LuongToan12/K4-Track-3B-Day24-GoldenFrieza-Eval-Guard

Trưởng nhóm/người nộp: Lương Khánh Toàn - 2A202602836

Ngày lab/deadline áp dụng: 2026-10-12 23:59 — Asia/Ho_Chi_Minh (UTC+07:00)

Commit dùng để chấm: HEAD (nhánh main)

Mỗi nhóm nộp một repo. Điền đủ thành viên và một mục INDIVIDUAL cho từng người.
Thêm/xóa rows để khớp nhóm thật; mẫu ba rows không ép nhóm phải có ba người.

## Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò / công việc thật | Bằng chứng |
|---|---|---|---|---|
| 1 | Lương Khánh Toàn | 2A202602836 | Thực hiện toàn bộ pipeline M1-M5, Phase A (`src/phase_a_ragas.py`), Phase B (`src/phase_b_judge.py`), Phase C (`src/phase_c_guard.py`), chạy live experiments và viết báo cáo phân tích | `src/phase_a_ragas.py`, `src/phase_b_judge.py`, `src/phase_c_guard.py`, `artifacts/*.json`, `doc/reports/*.md` |

Người tích hợp/chạy batch/nộp link: Lương Khánh Toàn (2A202602836) — tích hợp 5 module Day 18 (`m1_chunking.py`..`m5_enrichment.py`), chạy `scripts/setup_answers.py --live`, `scripts/run_experiments.py --phase all --live --latency-samples 20`, và kiểm chứng qua `scripts/check_lab.py --with-tests`.

## Môi trường và chuẩn bị trước lớp

OS/Python/compiler: Windows 11 (10.0.26100), Python 3.10.11 (64-bit), MSVC / Rust toolchain cho các gói nhị phân.
Virtualenv/dependencies/imports: Sử dụng môi trường `.venv` đã cài đặt đầy đủ `ragas`, `datasets`, `openai`, `qdrant-client`, `rank-bm25`, `sentence-transformers`, `presidio-analyzer`, `presidio-anonymizer`, `spacy` (`en_core_web_lg`), `nemoguardrails==0.10.0`, `jsonschema`. Kiểm tra bằng `pytest tests/ -m "not integration"` đạt 86 passed.
Models/Qdrant/50 answers đã chuẩn bị: Sử dụng Qdrant in-memory (`:memory:`), embedding `BAAI/bge-m3`, reranker `BAAI/bge-reranker-v2-m3`, LLM `gpt-4o-mini` và Ragas embeddings `text-embedding-3-small`. Tập `artifacts/answers_50q.json` được sinh live cho toàn bộ 50 câu hỏi (`factual`, `multi_hop`, `adversarial`) từ 107 chunks đã enrich metadata nguồn.
Runtime NeMo Guardrails hoạt động đầy đủ ở chế độ live với `LLMRails(RailsConfig.from_path("guardrails"))` kết hợp `self check input` và Colang 1.0 flows.

## INDIVIDUAL

### LuongKhanhToan-2A202602836

- Phần được giao và phần thực tế đã làm: Triển khai đầy đủ 5 module nền tảng từ Day 18 (`src/m1_chunking.py`, `src/m2_search.py`, `src/m3_rerank.py`, `src/m4_eval.py`, `src/m5_enrichment.py`) theo đúng hợp đồng `doc/PIPELINE_INTERFACE.md`; hoàn thiện toàn bộ Tasks 1–4 trong `src/phase_a_ragas.py` (chạy Ragas 50 câu, gom nhóm theo distribution, lập ma trận điểm yếu nhất và chẩn đoán 10 câu thấp điểm nhất), Tasks 5–8 trong `src/phase_b_judge.py` (pairwise judge 2 lượt đảo vị trí A/B, đo position bias & verbosity bias, binary judge và tính Cohen's Kappa với nhãn người), và Tasks 9a–12 trong `src/phase_c_guard.py` (custom Presidio recognizers cho CCCD/SĐT Việt Nam, NeMo Guardrails input/output rails, red-team 20 ca tấn công + 8 ca sạch + 4 ca đầu ra, đo latency P50/P95/P99).
- Bằng chứng: Mã nguồn trong `src/phase_a_ragas.py`, `src/phase_b_judge.py`, `src/phase_c_guard.py`, cấu hình `guardrails/config.yml` và `guardrails/rails.co`, bộ kết quả thực nghiệm live tại `artifacts/answers_50q.json`, `artifacts/ragas_50q.json`, `artifacts/judge_results.json`, `artifacts/guard_results.json`, cùng 3 báo cáo tại `doc/reports/failure_clusters.md`, `doc/reports/bias_report.md`, `doc/reports/blueprint.md`.
- Cách kiểm tra: Chạy kiểm thử đơn vị offline `pytest tests/ -m "not integration" -q` (86 passed) và chạy thực nghiệm live toàn diện qua `scripts/setup_answers.py --live`, `scripts/run_experiments.py --phase all --live --latency-samples 20`, sau đó xác thực toàn bộ hợp đồng dữ liệu bằng `python scripts/check_lab.py --with-tests` đạt 0 failed checks.
- Điều đã học: Hiểu rõ sự khác biệt giữa 4 chỉ số Ragas (`faithfulness`, `answer_relevancy`, `context_precision`, `context_recall`) khi phân tầng theo phân phối câu hỏi (`factual`, `multi_hop`, `adversarial`); nắm vững cơ chế phát hiện thiên lệch vị trí (position bias) bằng 2 lượt chấm đảo thứ tự A/B và hiệu chuẩn LLM-as-a-Judge với nhãn chuyên gia qua hệ số Cohen's Kappa; thiết kế kiến trúc phòng thủ nhiều lớp kết hợp bộ lọc biểu thức chính quy tốc độ cao (Presidio) với bộ kiểm duyệt ngữ nghĩa (NeMo Guardrails) và đánh đổi độ trễ P95.
- Giới hạn/cách xử lý: Hai file PDF scan ảnh (`BCTC.pdf` và `Nghi_dinh_so_13-2023_ve_bao_ve_du_lieu_ca_nhan_508ee.pdf`) không có text layer khiến truy hồi thiếu ngữ cảnh cho nhóm câu hỏi tài chính/nghị định; đã xử lý bằng cách ghi nhận rõ trong phân tích cụm lỗi và đề xuất bổ sung OCR pipeline. Ngoài ra, NER tiếng Anh mặc định của spaCy dễ nhận diện nhầm thực thể trên văn bản tiếng Việt nên đã giới hạn Presidio chỉ quét các thực thể PII mục tiêu (`VN_CCCD`, `VN_PHONE`, `EMAIL_ADDRESS`, `PHONE_NUMBER`), giúp tỷ lệ chặn nhầm trên tập clean giảm về 0%.
- Nguồn/AI hỗ trợ nếu có: Sử dụng trợ lý lập trình AI để rà soát hợp đồng schema JSON trong `doc/REPORT_SCHEMAS.md`, kiểm tra cú pháp Colang 1.0 của NeMo Guardrails và đối chiếu số liệu thống kê giữa các tệp `artifacts/*.json` với báo cáo Markdown; toàn bộ mã nguồn và kết quả đều được tự kiểm chứng lại bằng bộ test tự động và `scripts/check_lab.py`.

## Cập nhật sau khi nộp

Không có cập nhật sau deadline; bản nộp hiện tại là phiên bản chính thức hoàn chỉnh trước hạn.
