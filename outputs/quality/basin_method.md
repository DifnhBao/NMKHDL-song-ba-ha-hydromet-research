# Phương pháp xác định ranh giới lưu vực

## 1. Vị trí cửa ra

- **Công trình:** Thủy điện Sông Ba Hạ (220 MW), sông Ba
- **Tuyến đập (WGS84):** 13.0236263°N, 108.9039118°E
- **Nhà máy (WGS84):** 13.0653214°N, 108.9129319°E
- **Nguồn tọa độ:** OpenStreetMap way/480785944 (Đập thủy điện Sông Ba Hạ), OSM API 0.6
- **Đối tượng OSM:** way/480785944 (tuyến đập), way/827889670 (nhà máy),
  relation/7077710 (hồ chứa); lưu tại `data/raw/boundaries/osm_reference.geojson`
- **HYBAS_ID cửa ra:** 4121132660

## 2. Dữ liệu nền

- **Nguồn:** HydroBASINS v1c (HydroSHEDS, WWF)
- **Cấp:** Level 12 (chi tiết nhất)
- **Khu vực:** Châu Á (hybas_as_lev12_v1c)
- **Hệ tọa độ:** WGS84 (EPSG:4326)

## 3. Phương pháp

1. Xác định tuyến đập từ nguồn địa lý kiểm chứng được (OSM API 0.6).
2. Tìm tiểu lưu vực HydroBASINS **chứa** điểm tuyến đập (`contains`),
   không chọn theo diện tích gần đúng.
3. Truy vết ngược thượng nguồn bằng trường `NEXT_DOWN` (topology HydroBASINS).
4. Hợp nhất tất cả tiểu lưu vực thượng nguồn thành polygon lưu vực.
5. Tính diện tích bằng phép chiếu Albers Equal Area (không tính phẳng trên độ).
6. Kiểm tra chéo: polygon chứa điểm đập, cửa ra nằm trong tập thượng nguồn,
   tổng `SUB_AREA` khớp diện tích hình học.

## 4. Kết quả

- **Số tiểu lưu vực:** 82
- **Diện tích tính toán (Albers):** 11,160.6 km²
- **Tổng SUB_AREA của các tiểu lưu vực:** 11,202.5 km²
- **Diện tích tham khảo:** 11,115 km²
- **Sai lệch:** 0.41%
- **UP_AREA của tiểu lưu vực cửa ra:** theo HydroBASINS (xem `basin_validation.csv`)

## 5. Kiểm tra nghiệm thu (GATE 2)

| Kiểm tra | Kết quả |
|---|---|
| Điểm đập nằm trong polygon | ✅ ĐẠT — contains = True |
| Nhà máy nằm trong polygon | ✅ ĐẠT — contains = True |
| Cửa ra thuộc tập thượng nguồn | ✅ ĐẠT — HYBAS_ID 4121132660 ∈ 82 tiểu lưu vực |
| Hình học hợp lệ | ✅ ĐẠT — is_valid = True |
| Sai lệch diện tích ≤ 5% | ✅ ĐẠT — 0.41% |
| Diện tích hình học khớp tổng SUB_AREA (< 2%) | ✅ ĐẠT — 0.37% |

## 6. Đánh giá sai lệch diện tích

Sai lệch 0.41% nằm trong ngưỡng 5.0%. Theo V1.1 §8, vẫn phải kiểm tra hình học và mạng sông (đã thực hiện ở mục 5) trước khi sử dụng.

## 7. Giới hạn độ chính xác

- HydroBASINS dựa trên DEM toàn cầu; đường phân thủy có thể lệch cục bộ
  vài km, đặc biệt ở địa hình karst hoặc nơi sông đổi dòng.
- Tuyến đập lấy theo OSM (cộng đồng), chưa đối chiếu với hồ sơ thiết kế
  của chủ đầu tư; sai số vị trí ước tính < 500 m.
- Tiểu lưu vực chứa tuyến đập có diện tích cục bộ ~85 km²; phần diện tích
  nằm giữa tuyến đập và cửa ra của tiểu lưu vực được tính vào lưu vực,
  tạo sai lệch dương nhỏ (đã phản ánh trong sai lệch tổng).
- Ranh giới phải được người giám sát phê duyệt (GATE 2) trước khi dùng
  để tính mưa lưu vực.

## 8. Diễn giải bản đồ F01

F01 hiển thị polygon lưu vực đến tuyến đập (màu xanh ngọc), mạng tiểu lưu vực
HydroBASINS level 12 làm nền định vị (đường xám), hồ Sông Ba Hạ và tuyến đập
theo OSM. Điểm kiểm tra (tam giác đỏ) trùng tuyến đập và **nằm trong** polygon;
nhà máy (vuông tím) nằm hạ lưu ~4,9 km nhưng vẫn trong cùng tiểu lưu vực.
Bản đồ dùng để nghiệm thu GATE 2, không dùng để đọc giá trị mưa.

## 9. Trạng thái phê duyệt

- **CHẤP NHẬN CÓ ĐIỀU KIỆN** theo quyết định của trưởng nhóm ngày 27/10/2026; sử dụng polygon như đại diện lưu vực xấp xỉ cho nghiên cứu.
- Kết quả hình học/diện tích nêu trên không chứng minh ranh giới khớp hoàn toàn tuyến đập; nguồn tọa độ OSM là dữ liệu cộng đồng.
- Việc phê duyệt polygon **không phải** nghiệm thu cuối phương pháp tính mưa hoặc toàn đề tài. Xem `docs/OWNER_DECISIONS_2026-10-27.md` và `outputs/quality/gate2_approval.json`.

## 10. Định dạng đầu ra

- `song_ba_ha_catchment.geojson`: Polygon lưu vực (WGS84)
- `basin_validation.csv`: Thông tin diện tích và kiểm tra
- `F01_basin_map.png`: Bản đồ kiểm chứng
