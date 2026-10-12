# Đánh giá LLM Judge Phase B

Nhóm: GoldenFrieza

Người phụ trách: Lương Khánh Toàn - 2A202602836

Nguồn: `artifacts/judge_results.json`; run timestamp: 2026-10-12T10:18:47.812102+00:00.
Models generation/judge: generation=`["gpt-4o-mini-2024-07-18"]`, judge=`["gpt-4o-mini"]`.

## Năm cặp A/B và hai lượt

Nguồn cố định: A từ `artifacts/answers_50q.json:answer`; B từ
`fixtures/human_labels_10q.json:model_answer`; reference từ `fixtures/test_set_50q.json:ground_truth`.
Ids: 1, 5, 12, 21, 41. Không đổi nguồn sau khi xem kết quả judge.

| ID | Candidate A (`answers_50q.json`) | Candidate B (`human_labels_10q.json`) | winner_pass1 | winner_pass2 (quy về A/B gốc) | final_winner | position_consistent | Điểm Pass 1 (A / B) | Điểm Pass 2 (A / B gốc) | Lý do hai lượt (Pass 1 & Pass 2) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Nhân viên được nghỉ 3 ngày làm việc khi kết hôn. (48 ký tự) | Nhân viên được nghỉ 3 ngày làm việc có lương khi kết hôn. (57 ký tự) | B | B | B | true | 0.7 / 1.0 | 0.8 / 1.0 | Pass 1: B nêu đầy đủ việc nghỉ có lương, A thiếu chi tiết này. Pass 2: Khi đảo B lên vị trí đầu, judge vẫn chọn B gốc vì đầy đủ thông tin nghỉ có lương. |
| 5 | Cần phê duyệt của Trưởng phòng và Kế toán trưởng. (49 ký tự) | Cần Giám đốc phòng ban phê duyệt. (33 ký tự) | B | A | tie | false | 0.2 / 0.6 | 0.6 / 0.2 | Pass 1: Chọn B (0.6) vì cho rằng gần đúng hơn A. Pass 2: Đảo vị trí thì chọn A gốc (nằm ở vị trí thứ hai trong prompt Pass 2) với cùng lý do cả hai đều sai so với đáp án chuẩn (Tổng Giám đốc). |
| 12 | Thưởng Tết tối thiểu cho nhân viên chính thức có từ 6 tháng trở lên là **1 tháng lương**. (89 ký tự) | Nhân viên được thưởng Tết tối thiểu 1 tháng lương. (50 ký tự) | A | A | A | true | 1.0 / 0.7 | 1.0 / 0.8 | Pass 1: A nêu đầy đủ điều kiện nhân viên chính thức từ 6 tháng trở lên, B bỏ sót điều kiện thời gian. Pass 2: Vẫn chọn A gốc (1.0) nhờ diễn đạt đầy đủ điều kiện. |
| 21 | Nhân viên có 9 năm thâm niên được nghỉ 18 ngày phép năm (15 + 3). Về lương, không tìm thấy thông tin cụ thể trong các tài liệu đã cho. (134 ký tự) | Được nghỉ 18 ngày phép (15 cơ bản + 3 thâm niên). Lương Senior từ 20 đến 35 triệu. (82 ký tự) | B | B | B | true | 0.7 / 1.0 | 0.7 / 1.0 | Pass 1: B trả lời đủ cả số ngày phép (18 ngày) lẫn dải lương Senior (20–35 triệu), trong khi A thiếu thông tin lương. Pass 2: Vẫn chọn B gốc (1.0) một cách nhất quán. |
| 41 | Mỗi nhân viên chính thức được hưởng **15 ngày phép năm** có lương. (66 ký tự) | Nhân viên được nghỉ 12 ngày phép năm. (37 ký tự) | A | A | A | true | 1.0 / 0.0 | 1.0 / 0.2 | Pass 1: A đúng theo chính sách hiện hành v2024 (15 ngày), B sai do dùng chính sách cũ v2023 (12 ngày). Pass 2: Vẫn chọn A gốc (1.0) nhất quán. |

Position bias count/rate: 1 / 5 cặp (rate = 0.20 hay 20.0%).
Verbosity win rate: 0.75 (75.0%); decisive cases: 4 (`a_wins_a_longer = 2`, `b_wins_b_longer = 1`, `total_decisive = 4`).

**Phân tích các trường hợp không nhất quán và hiện tượng câu dài hơn thắng:**
- **Trường hợp bất nhất vị trí (ID 5):** Theo ground truth, đơn mua thiết bị 55 triệu VNĐ (> 50 triệu VNĐ) phải do **Tổng Giám đốc** phê duyệt (cấp 3). Cả Candidate A ("Trưởng phòng và Kế toán trưởng" — quy trình tạm ứng/cấp thấp) lẫn Candidate B ("Giám đốc phòng ban" — cấp 2 cho 10–50 triệu) đều sai thực tế. Khi cả hai ứng viên đều sai, LLM Judge (`gpt-4o-mini`) rơi vào trạng thái phân vân và phát sinh **recency/second-position bias**: ở cả Pass 1 và Pass 2, mô hình đều chấm 0.6 cho phương án nằm ở vị trí thứ hai trong prompt và 0.2 cho phương án đầu tiên. Cơ chế đảo vị trí 2 lượt và gán `final_winner = "tie"` đã phát hiện và trung hòa chính xác sai lệch này.
- **Phân biệt thống kê Verbosity Win Rate (0.75) với nguyên nhân thực chất:** Về mặt thống kê thuần túy, trong 4 cặp có kết quả phân định (`final_winner != "tie"`), có 3 cặp phần thắng thuộc về câu dài hơn (ID 1: B dài 57 > A 48 ký tự; ID 12: A dài 89 > B 50 ký tự; ID 41: A dài 66 > B 37 ký tự). Tuy nhiên, xét về nội dung, cả 3 câu thắng này dài hơn là do **chứa thêm thông tin điều kiện quan trọng khớp với reference** (ID 1 có cụm "có lương", ID 12 có điều kiện "chính thức có từ 6 tháng trở lên", ID 41 nêu đúng "15 ngày phép năm có lương" theo v2024). Bằng chứng đối chứng rõ nhất là **ID 21**: Candidate A dài hơn đáng kể (134 ký tự so với 82 ký tự của B) nhưng lại thiếu vế khoảng lương ("Về lương, không tìm thấy thông tin cụ thể..."), và Judge đã chấm B thắng tuyệt đối (1.0 vs 0.7) ở cả hai lượt. Do đó, con số `verbosity_bias = 0.75` trên mẫu nhỏ 4 cặp phản ánh sự tương quan giữa độ đầy đủ thông tin và độ dài câu, chứ không phải Judge mù quáng thiên vị câu dài dòng.

## Calibration đúng model_answer

Helper đánh giá đúng `question`/`model_answer` đang có trong `fixtures/human_labels_10q.json`;
không lấy answer mới của pipeline. Prompt chỉ nhận `question`, `answer`, `reference`.
Không gửi `human_label`, `human_note` hoặc phân bố nhãn human vào prompt.

| question_id | model_answer gốc (`human_labels_10q.json`) | Nhãn Judge (0/1) | Nhãn Human (0/1) | Agree | Lý do của Judge (`reasoning`) |
|---|---|---|---|---|---|
| 1 | Nhân viên được nghỉ 3 ngày làm việc có lương khi kết hôn. | 1 | 1 | true | Câu trả lời chính xác theo reference, đầy đủ thông tin về số ngày nghỉ và điều kiện không trừ vào phép năm. |
| 5 | Cần Giám đốc phòng ban phê duyệt. | 0 | 0 | true | Câu trả lời sai vì yêu cầu phê duyệt cho đơn hàng trên 50 triệu là từ Tổng Giám đốc, không phải Giám đốc phòng ban. |
| 12 | Nhân viên được thưởng Tết tối thiểu 1 tháng lương. | 1 | 1 | true | Câu trả lời chính xác theo reference, nêu rõ điều kiện và mức thưởng cho nhân viên chính thức có từ 6 tháng trở lên. |
| 21 | Được nghỉ 18 ngày phép (15 cơ bản + 3 thâm niên). Lương Senior từ 20 đến 35 triệu. | 1 | 1 | true | Câu trả lời chính xác theo reference, nêu rõ số ngày phép và khoảng lương cho nhân viên Senior với 9 năm thâm niên. |
| 23 | Hoàn trả 25 triệu vì chưa đủ 1 năm cam kết. | 1 | 1 | true | Câu trả lời chính xác theo thông tin trong reference, nêu rõ nhân viên phải hoàn trả 25 triệu do chưa đủ 1 năm cam kết. |
| 29 | Trưởng phòng phê duyệt. Phạt 2% tháng trên 8 triệu. | 0 | 0 | true | Câu trả lời sai vì không đề cập đến sự cần thiết có sự phê duyệt của Kế toán trưởng bên cạnh Trưởng phòng. Ngoài ra, phí phạt được tính cho 15 ngày quá hạn, không phải là 2% trên 8 triệu mà là 80.000 VNĐ. |
| 33 | Phép: 19 ngày. Phụ cấp: 1.500.000 VNĐ/tháng. | 1 | 1 | true | Câu trả lời cung cấp đúng số ngày phép và tổng phụ cấp hàng tháng theo thông tin trong tài liệu tham khảo. |
| 41 | Nhân viên được nghỉ 12 ngày phép năm. | 0 | 0 | true | Câu trả lời sai vì nó dựa trên chính sách cũ (v2023) thay vì chính sách hiện hành (v2024) là 15 ngày phép năm. |
| 46 | Nhân viên thử việc không được nghỉ phép năm và phải xin nghỉ không lương nếu cần. | 1 | 1 | true | Câu trả lời chính xác theo reference, nêu rõ rằng nhân viên thử việc không được nghỉ phép năm và phải xin nghỉ không lương nếu cần, đồng thời không bỏ qua điều kiện cần có sự phê duyệt của trưởng phòng. |
| 50 | Được, miễn là đảm bảo kết nối an toàn. | 0 | 0 | true | Câu trả lời sai vì khẳng định rằng nhân viên Manager có thể dùng VPN cá nhân khi WFH, trong khi reference rõ ràng cấm việc này. |

Cohen’s κ: 1.0000 (`1.0`).
Observed/chance agreement và diễn giải:
- Số câu đồng thuận thực tế: 10/10 câu $\Rightarrow P_o = \frac{10}{10} = 1.00$.
- Phân bố nhãn Judge: 6 nhãn `1`, 4 nhãn `0`. Phân bố nhãn Human: 6 nhãn `1`, 4 nhãn `0`.
- Xác suất đồng thuận ngẫu nhiên: $P_e = P(\text{Judge}=1)\cdot P(\text{Human}=1) + P(\text{Judge}=0)\cdot P(\text{Human}=0) = 0.6 \times 0.6 + 0.4 \times 0.4 = 0.36 + 0.16 = 0.52$.
- Hệ số Cohen's Kappa: $\kappa = \frac{P_o - P_e}{1 - P_e} = \frac{1.00 - 0.52}{1.00 - 0.52} = 1.0000$.
- Diễn giải: Mức đồng thuận hoàn hảo ($\kappa = 1.0 > 0.6$) trên 10 câu mẫu nhờ rubric nhị phân quy định rõ tiêu chí: chấm `1` khi câu trả lời nêu đúng kết luận cốt lõi và không mâu thuẫn với bẫy phiên bản/phủ định, và chấm `0` khi sai số liệu, sai cấp phê duyệt (câu 5, 29), dùng phiên bản chính sách cũ (câu 41) hoặc đảo ngược quy định cấm (câu 50).

## Giới hạn và cách dùng judge

- **Giới hạn kích thước mẫu và mô hình:** Tập đánh giá Pairwise chỉ gồm 5 cặp (`N = 5`) và tập Calibration chỉ gồm 10 câu (`N = 10`). Với cỡ mẫu nhỏ này, một câu lệch duy nhất đã làm thay đổi 20% `position_bias_rate` hoặc làm giảm mạnh $\kappa$. Hơn nữa, cả hệ thống sinh câu trả lời (`gpt-4o-mini-2024-07-18`) và hệ thống chấm (`gpt-4o-mini`) đều thuộc cùng họ mô hình `gpt-4o-mini`, nên tiềm ẩn nguy cơ **self-preference bias** (mô hình chấm ưa thích văn phong trình bày của chính nó).
- **Trường hợp nhạy cảm / ranh giới cần lưu ý:** Ở các câu `question_id = 12` và `question_id = 46`, `model_answer` trong tập calibration hơi rút gọn điều kiện phụ (ví dụ câu 46 không nhắc cụm "được trưởng phòng đồng ý", câu 12 không lặp lại cụm "từ 6 tháng trở lên"). Nhờ rubric hướng dẫn chấp nhận câu trả lời ngắn gọn miễn đúng kết luận chính, Judge đã khớp với nhãn `1` của Human. Tuy nhiên, trong phần chấm Pairwise (câu 12), khi đặt cạnh một câu trả lời đầy đủ điều kiện hơn, Judge chấm câu rút gọn thấp điểm hơn (0.7–0.8 so với 1.0).
- **Nguyên tắc vận hành thực tế:** Không bao giờ coi LLM-as-a-Judge là chân lý tuyệt đối. Khi đưa vào pipeline đánh giá tự động:
  1. Bắt buộc chạy **2 lượt đảo vị trí (swap-order mitigation)** cho mọi phép so sánh cặp và chuyển các trường hợp bất nhất thành `tie` để loại bỏ position bias.
  2. Định kỳ lấy mẫu ngẫu nhiên (5–10% lượng câu hỏi sản phẩm hoặc các ca `tie`/điểm sát ngưỡng) để chuyên gia con người gán nhãn lại và theo dõi độ trượt của Cohen's $\kappa$ theo thời gian.
