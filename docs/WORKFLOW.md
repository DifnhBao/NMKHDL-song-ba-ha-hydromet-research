# Quy trình phối hợp và nghiệm thu

**Nguồn yêu cầu:** [Đặc tả V1.0](DAC_TA_NGHIEN_CUU_V1.0.md) và [Phụ lục V1.1](PHU_LUC_TRIEN_KHAI_V1.1.md).

1. Người thực hiện nhận gói thủy văn 36 tháng qua kênh riêng, giải nén vào `data/raw/hydrology/`. Không đưa ZIP, dữ liệu thô hoặc API token lên repository.
2. Mỗi cổng nghiệm thu tương ứng một GitHub Issue #1–#6; ưu tiên công việc P0 theo V1.1.
3. Trước khi dùng polygon để tính mưa lưu vực, gửi `F01_basin_map.png`, `basin_method.md` và `basin_validation.csv` cho người thiết kế phê duyệt (GATE 2).
4. Mã nguồn triển khai trên nhánh `feature/<gate>-<short-name>`; mở Pull Request liên kết Issue. Trình bày các kết quả QA và cách tái lập trong PR.
5. Không tự sửa dữ liệu gốc, bỏ cực trị, thay nguồn chính, thay câu hỏi nghiên cứu hoặc phạm vi khi chưa được phê duyệt.
6. Hoàn thành GATE 6 khi `handoff_writer/` chứa bảng, hình, diễn giải, nguồn tham khảo và hướng dẫn tái lập theo V1.1.

## Bàn giao trong PR
- Tên Issue và đầu ra cụ thể.
- Lệnh chạy và phiên bản dữ liệu.
- Kết quả kiểm tra chất lượng, trường hợp ngoại lệ.
- Giới hạn, đề xuất xử lý cần phê duyệt.

**Bộ dữ liệu 2023–2025 nằm ngoài Git và được truyền nội bộ**. Không suy luận bộ dữ liệu đã được đưa lên GitHub chỉ từ việc có cấu trúc thư mục.
