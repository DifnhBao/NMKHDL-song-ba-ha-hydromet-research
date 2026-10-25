# Song Ba Ha Hydrometeorological Data Research

**Học phần:** Nhập môn Khoa học dữ liệu  
**Đề tài:** Nghiên cứu dữ liệu lĩnh vực khí tượng thủy văn, xử lý và trực quan hóa dữ liệu và rút ra các ý nghĩa.  
**Phạm vi:** Lưu vực sông Ba đến Thủy điện Sông Ba Hạ; giai đoạn 2023–2025.  
**Trạng thái:** Đang triển khai; dữ liệu gốc 36 tháng được bàn giao **ngoài Git**.

## Tài liệu bắt buộc

- [Đặc tả nghiên cứu V1.0](docs/DAC_TA_NGHIEN_CUU_V1.0.md)
- [Hướng dẫn triển khai, bàn giao và nghiệm thu V1.1](docs/PHU_LUC_TRIEN_KHAI_V1.1.md)
- [Quy trình làm việc GitHub](docs/WORKFLOW.md)
- [GitHub Issues — sáu GATE](../../issues)

**Ưu tiên:** Đọc V1.1 và tiến hành Issues #1–#6 theo thứ tự phụ thuộc. Những quyết định tác động đến tính đúng đắn khoa học cần người thiết kế phê duyệt.

## Mục tiêu

- **RQ1:** Phân tích khí tượng: mưa CHIRPS v3 Final, nhiệt độ ERA5-Land và tính mùa.
- **RQ2:** Phân tích thủy văn: lưu lượng nước về hồ, mực nước và các sự kiện đáng chú ý.
- **RQ3:** Phân tích quan hệ thống kê giữa mưa lưu vực và lưu lượng về hồ tại quy mô tháng, độ trễ 0 và 1 tháng; không diễn giải thành quan hệ nhân quả.

## Cấu trúc

```text
docs/                # Đặc tả và quy trình
scripts/             # Mã kiểm định, xử lý không gian, khí tượng, phân tích
data/raw/            # Dữ liệu nguồn (không commit)
data/interim/        # Dữ liệu trung gian (không commit)
data/processed/      # Dữ liệu kết quả (không commit)
outputs/figures/     # Biểu đồ
outputs/tables/      # Bảng thống kê
outputs/quality/     # Báo cáo QA
outputs/maps/        # Bản đồ
handoff_writer/      # Sản phẩm để viết báo cáo
```

## Bắt đầu

1. Clone repository và chuẩn bị Python 3.11+.
2. Tạo môi trường ảo, chạy `pip install -r requirements.txt`.
3. Nhận và giải nén dữ liệu Sông Ba Hạ 2023–2025 vào `data/raw/hydrology/`.
4. Thực hiện [Issue #1](../../issues/1) kiểm định dữ liệu; triển khai [Issue #2](../../issues/2) xác định lưu vực.
5. Chỉ sau khi polygon được nghiệm thu mới trích mưa CHIRPS để phân tích quan hệ mưa – dòng chảy.

Các script chi tiết sẽ do thành viên kỹ thuật triển khai theo V1.1; README này không có nghĩa toàn bộ pipeline đã hoàn thành.

## Nguồn dữ liệu

- [Sông Ba Hạ](https://sbh.vn/vi-VN/san-xuat/Tinh-hinh-san-xuat-60-1300)
- [CHIRPS v3](https://www.chc.ucsb.edu/data/chirps3)
- [ERA5-Land](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land)
- [HydroBASINS](https://www.hydrosheds.org/products/hydrobasins)

**Không đưa dữ liệu lớn, thông tin đăng nhập, key hoặc dữ liệu chưa được phép chia sẻ lên repository.**
