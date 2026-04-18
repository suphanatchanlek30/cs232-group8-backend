# เอกสารทดสอบ API (TEST_API)

## 1. ชื่อเอกสาร
TEST_API.md - คู่มือทดสอบ API ของ TU Pulse Backend

## 2. เอกสารนี้คืออะไร
เอกสารนี้สรุปวิธีรันระบบ และวิธีทดสอบทุก endpoint ที่มีอยู่จริงในโค้ดปัจจุบัน (หลังปรับให้สอดคล้องกับ API Space) เพื่อให้สมาชิกใหม่สามารถเปิด Postman แล้วทดสอบตามได้ทันที

## 3. สถานะโปรเจกต์ตอนนี้ (Phase)
- Phase: Backend API Contract Alignment + Integration Test Guide
- โค้ดมี endpoint ใช้งานจริงครบทุกหมวดหลัก: auth, public, reports, tracking, dashboard, incidents, notifications, admin, analytics
- มีบางจุดที่ยังเป็นข้อจำกัดเชิง implementation (ระบุในหัวข้อ "Endpoint ที่ยังไม่พร้อมใช้งานเต็มรูปแบบ")

## 4. วิธีรันระบบ
### 4.1 เปิด virtual environment
PowerShell:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 4.2 เปิด database
วิธีที่แนะนำ (Docker Compose):
```powershell
docker compose up -d db
```

### 4.3 รัน migration
โปรเจกต์นี้ยังไม่มี Alembic migration แยกไฟล์
- ใช้การสร้างตารางผ่าน SQLAlchemy `create_all` ใน startup (`AUTO_CREATE_TABLES=true`)
- ถ้ารันผ่าน app แล้ว DB ว่าง ระบบจะสร้าง table ให้อัตโนมัติ

### 4.4 รัน seed (ถ้ามี)
```powershell
python -m app.db.seed_staff
```
seed จะสร้าง unit และ user ตัวอย่าง เช่น
- `security@tu.ac.th` (STAFF)
- `admin@tu.ac.th` (ADMIN)

### 4.5 รัน server
```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4.6 Base URL
- API Base URL: `http://localhost:8000/api/v1`
- Health/Root: `http://localhost:8000/`
- Swagger: `http://localhost:8000/docs`

## 5. วิธีตั้งค่า Postman
### 5.1 Collection name
แนะนำชื่อ: `TU Pulse API (Local)`

### 5.2 Environment variables
สร้าง Postman Environment เช่น `TU Pulse Local` แล้วใส่:
- `baseUrl` = `http://localhost:8000/api/v1`
- `reporterAccessToken` = ``
- `reporterRefreshToken` = ``
- `staffAccessToken` = ``
- `staffRefreshToken` = ``
- `adminAccessToken` = ``
- `adminRefreshToken` = ``
- `trackingCode` = ``
- `reportId` = ``
- `incidentId` = ``
- `notificationId` = ``
- `unitId` = ``

## 6. ลำดับการทดสอบที่แนะนำ
1. Root health
2. Public endpoints
3. LIFF auth (Reporter)
4. Staff auth (Staff/Admin)
5. Reports
6. Tracking
7. Dashboard
8. Incidents + Incident actions
9. Notifications
10. Admin
11. Analytics

## 7. รายละเอียดการทดสอบทุก endpoint

### 7.1 Root Health
1. **Root health check**
- Method: `GET`
- URL: `http://localhost:8000/`
- Role: Public
- Headers: None
- Query Params: None
- Path Params: None
- Body: None
- วิธีทดสอบใน Postman: ส่ง request ตรง
- Expected Status Code: `200`
- Expected Response ตัวอย่าง:
```json
{
  "success": true,
  "message": "TU Pulse Backend is running",
  "data": {
    "appName": "TU Pulse Backend",
    "env": "development"
  }
}
```
- หมายเหตุ: ใช้เช็กว่า server ติด

### 7.2 LIFF Auth (Reporter)
2. **LIFF Exchange**
- Method: `POST`
- URL: `{{baseUrl}}/liff/auth/exchange`
- Role: Public
- Headers: `Content-Type: application/json`
- Query Params: None
- Path Params: None
- Body ตัวอย่าง:
```json
{
  "idToken": "mock-line-token-testuser001",
  "displayName": "Arm",
  "pictureUrl": "https://profile.line/abc.jpg"
}
```
- วิธีทดสอบใน Postman: ส่ง body ตามตัวอย่าง แล้วเก็บ token ลง environment
- Expected Status Code: `200`
- Expected Response ตัวอย่าง:
```json
{
  "success": true,
  "message": "เข้าสู่ระบบผ่าน LINE สำเร็จ",
  "data": {
    "accessToken": "...",
    "refreshToken": "...",
    "user": {
      "userId": "...",
      "lineUserId": "testuser001",
      "fullName": "Arm",
      "role": "REPORTER"
    }
  }
}
```
- หมายเหตุ: ในโหมด `LINE_VERIFY_MODE=mock` ต้องขึ้นต้น `mock-line-token-`

3. **LIFF Refresh**
- Method: `POST`
- URL: `{{baseUrl}}/liff/auth/refresh`
- Role: Reporter token owner
- Headers: `Content-Type: application/json`
- Body ตัวอย่าง:
```json
{
  "refreshToken": "{{reporterRefreshToken}}"
}
```
- Expected Status Code: `200`
- Expected Response ตัวอย่าง:
```json
{
  "success": true,
  "message": "ต่ออายุ token สำเร็จ",
  "data": {
    "accessToken": "..."
  }
}
```
- หมายเหตุ: ถ้า refresh token ถูก revoke จะได้ `403`

4. **LIFF Logout**
- Method: `POST`
- URL: `{{baseUrl}}/liff/auth/logout`
- Role: Reporter token owner
- Headers: `Content-Type: application/json`
- Body ตัวอย่าง:
```json
{
  "refreshToken": "{{reporterRefreshToken}}"
}
```
- Expected Status Code: `200`
- Expected Response ตัวอย่าง:
```json
{
  "success": true,
  "message": "ออกจากระบบสำเร็จ",
  "data": null
}
```
- หมายเหตุ: หลัง logout แล้ว token เดิม refresh ไม่ได้

5. **LIFF Me**
- Method: `GET`
- URL: `{{baseUrl}}/liff/auth/me`
- Role: Authenticated Reporter
- Headers: `Authorization: Bearer {{reporterAccessToken}}`
- Body: None
- Expected Status Code: `200`
- Expected Response ตัวอย่าง:
```json
{
  "success": true,
  "message": "ดึงข้อมูลผู้ใช้สำเร็จ",
  "data": {
    "userId": "...",
    "fullName": "Arm",
    "lineDisplayName": "Arm",
    "role": "REPORTER",
    "reporterType": "STUDENT"
  }
}
```
- หมายเหตุ: ถ้าไม่ส่ง token จะโดน `403` จาก HTTPBearer

### 7.3 Staff Auth
6. **Staff Login**
- Method: `POST`
- URL: `{{baseUrl}}/staff/auth/login`
- Role: Public
- Headers: `Content-Type: application/json`
- Body ตัวอย่าง:
```json
{
  "email": "security@tu.ac.th",
  "password": "Password123!"
}
```
- Expected Status Code: `200`
- Expected Response ตัวอย่าง:
```json
{
  "success": true,
  "message": "เข้าสู่ระบบสำเร็จ",
  "data": {
    "accessToken": "...",
    "refreshToken": "...",
    "user": {
      "userId": "...",
      "fullName": "Somying Jaidee",
      "email": "security@tu.ac.th",
      "role": "STAFF",
      "unit": {
        "unitId": "...",
        "name": "Security"
      }
    }
  }
}
```
- หมายเหตุ: ต้องมี seed user หรือ user ที่สร้างแล้ว

7. **Staff Refresh**
- Method: `POST`
- URL: `{{baseUrl}}/staff/auth/refresh`
- Role: Staff/Admin token owner
- Headers: `Content-Type: application/json`
- Body:
```json
{
  "refreshToken": "{{staffRefreshToken}}"
}
```
- Expected Status Code: `200`
- Expected Response: `{ success, message, data.accessToken }`

8. **Staff Logout**
- Method: `POST`
- URL: `{{baseUrl}}/staff/auth/logout`
- Role: Staff/Admin token owner
- Headers: `Content-Type: application/json`
- Body:
```json
{
  "refreshToken": "{{staffRefreshToken}}"
}
```
- Expected Status Code: `200`
- Expected Response: `{ success: true, message: "ออกจากระบบสำเร็จ", data: null }`

9. **Staff Me**
- Method: `GET`
- URL: `{{baseUrl}}/staff/auth/me`
- Role: Authenticated Staff/Admin
- Headers: `Authorization: Bearer {{staffAccessToken}}`
- Expected Status Code: `200`
- Expected Response: มี `permissions` array

### 7.4 Public
10. **Public System Info**
- Method: `GET`
- URL: `{{baseUrl}}/public/system-info`
- Role: Public
- Expected Status Code: `200`
- Expected Response fields: `systemName`, `projectNameEn`, `allowReportSubmission`, `version`

11. **Public Report Options**
- Method: `GET`
- URL: `{{baseUrl}}/public/report-options`
- Role: Public
- Expected Status Code: `200`
- Expected Response fields: `incidentLabels`, `reporterTypes`

12. **Public Locations**
- Method: `GET`
- URL: `{{baseUrl}}/public/locations`
- Role: Public
- Query Params: `search`, `page`, `pageSize`
- Expected Status Code: `200`
- Expected Response: paginated `items + pagination`

### 7.5 Reports
13. **Create Report (JSON)**
- Method: `POST`
- URL: `{{baseUrl}}/reports`
- Role: Authenticated Reporter
- Headers: `Authorization: Bearer {{reporterAccessToken}}`, `Content-Type: application/json`
- Body ตัวอย่าง:
```json
{
  "sourceChannel": "LIFF",
  "reportText": "มีขยะล้นหน้าตึก LC",
  "voiceText": null,
  "normalizedText": "มีขยะล้นหน้าตึก LC",
  "reporterType": "STUDENT",
  "label": "waste_issue",
  "occurredAt": "2026-04-12T20:10:00+07:00",
  "location": {
    "locationName": "หน้าตึก LC",
    "lat": 14.072,
    "lng": 100.601
  },
  "attachments": [
    {
      "fileKey": "reports/2026/04/rpt_xxx/trash.jpg",
      "fileUrl": "https://..."
    }
  ]
}
```
- Expected Status Code: `201`
- Expected Response ตัวอย่าง:
```json
{
  "success": true,
  "message": "ส่งรายงานแจ้งเหตุสำเร็จ",
  "data": {
    "reportId": "...",
    "trackingCode": "TP-...",
    "incidentId": "...",
    "isMerged": true,
    "status": "LINKED_TO_INCIDENT",
    "candidateIncidentType": "waste_issue"
  }
}
```
- หมายเหตุ: ถ้าไม่มี label อาจได้ `incidentId=null` และ `status=SUBMITTED`

14. **Create Report (Multipart)**
- Method: `POST`
- URL: `{{baseUrl}}/reports/multipart`
- Role: Authenticated Reporter
- Headers: `Authorization: Bearer {{reporterAccessToken}}`
- Body (form-data): `reportText`, `voiceText`, `label`, `occurredAt`, `locationName`, `lat`, `lng`, `images[]`
- Expected Status Code: `201`
- Expected Response: shape เดียวกับ create JSON

15. **Get My Reports**
- Method: `GET`
- URL: `{{baseUrl}}/reports/my`
- Role: Authenticated Reporter
- Headers: `Authorization: Bearer {{reporterAccessToken}}`
- Query Params: `page`, `pageSize`, `status`
- Expected Status Code: `200`
- Expected Response: paginated reports

16. **Get Report Detail**
- Method: `GET`
- URL: `{{baseUrl}}/reports/{{reportId}}`
- Role: Reporter owner หรือ Staff/Admin
- Headers: `Authorization: Bearer {{reporterAccessToken}}` หรือ `{{staffAccessToken}}`
- Expected Status Code: `200`
- Expected Response fields: `reportText`, `voiceText`, `detectedLabels`, `linkedIncidentId`, `attachments`, `submittedAt`

### 7.6 Tracking
17. **Track by Code**
- Method: `GET`
- URL: `{{baseUrl}}/tracking/{{trackingCode}}`
- Role: Public
- Expected Status Code: `200`
- Expected Response fields: `trackingCode`, `reportId`, `incidentId`, `incidentType`, `status`, `severity`, `assignedUnit`, `latestUpdatedAt`

18. **My Incidents**
- Method: `GET`
- URL: `{{baseUrl}}/tracking/my-incidents`
- Role: Authenticated Reporter
- Headers: `Authorization: Bearer {{reporterAccessToken}}`
- Query Params: `page`, `pageSize`
- Expected Status Code: `200`
- Expected Response: paginated incidents

19. **Tracking Timeline**
- Method: `GET`
- URL: `{{baseUrl}}/tracking/{{trackingCode}}/timeline`
- Role: Public
- Expected Status Code: `200`
- Expected Response: `data.timeline[]` (มี `status`, `changedAt`, `note`)

### 7.7 Dashboard
20. **Dashboard Summary**
- Method: `GET`
- URL: `{{baseUrl}}/dashboard/summary`
- Role: Staff/Admin
- Headers: `Authorization: Bearer {{staffAccessToken}}`
- Query Params: `dateFrom`, `dateTo`, `unitId`
- Expected Status Code: `200`
- Expected Response fields: `totalIncidents`, `newCount`, `inReviewCount`, `inProgressCount`, `resolvedCount`, `highSeverityCount`

### 7.8 Incidents (Dashboard + Actions)
21. **List Incidents**
- Method: `GET`
- URL: `{{baseUrl}}/incidents`
- Role: Staff/Admin
- Headers: `Authorization: Bearer {{staffAccessToken}}`
- Query Params: `page`, `pageSize`, `status`, `severity`, `incidentType`, `assignedUnitId`, `search`, `dateFrom`, `dateTo`, `sortBy`, `sortOrder`
- Expected Status Code: `200`
- Expected Response: paginated incidents

22. **Incident Detail**
- Method: `GET`
- URL: `{{baseUrl}}/incidents/{{incidentId}}`
- Role: Staff/Admin
- Headers: `Authorization: Bearer {{staffAccessToken}}`
- Expected Status Code: `200`

23. **Incident Reports**
- Method: `GET`
- URL: `{{baseUrl}}/incidents/{{incidentId}}/reports`
- Role: Staff/Admin
- Headers: `Authorization: Bearer {{staffAccessToken}}`
- Query Params: `page`, `pageSize`
- Expected Status Code: `200`

24. **Incident Timeline**
- Method: `GET`
- URL: `{{baseUrl}}/incidents/{{incidentId}}/timeline`
- Role: Staff/Admin
- Headers: `Authorization: Bearer {{staffAccessToken}}`
- Expected Status Code: `200`

25. **Update Incident Status**
- Method: `PATCH`
- URL: `{{baseUrl}}/incidents/{{incidentId}}/status`
- Role: Staff/Admin
- Headers: `Authorization: Bearer {{staffAccessToken}}`, `Content-Type: application/json`
- Body:
```json
{
  "status": "IN_PROGRESS",
  "note": "มอบหมายเจ้าหน้าที่เข้าตรวจสอบแล้ว"
}
```
- Expected Status Code: `200`
- Expected Response fields: `incidentId`, `status`, `updatedAt`

26. **Assign Unit**
- Method: `PATCH`
- URL: `{{baseUrl}}/incidents/{{incidentId}}/assign-unit`
- Role: Staff/Admin
- Headers: `Authorization: Bearer {{staffAccessToken}}`
- Body:
```json
{
  "assignedUnitId": "{{unitId}}",
  "note": "ส่งต่อให้ฝ่ายอาคารสถานที่"
}
```
- Expected Status Code: `200`

27. **Update Priority (Severity)**
- Method: `PATCH`
- URL: `{{baseUrl}}/incidents/{{incidentId}}/priority`
- Role: Staff/Admin
- Headers: `Authorization: Bearer {{staffAccessToken}}`
- Body:
```json
{
  "severity": "HIGH",
  "reason": "อยู่ใกล้ห้อง server"
}
```
- Expected Status Code: `200`

28. **Resolve Incident**
- Method: `POST`
- URL: `{{baseUrl}}/incidents/{{incidentId}}/resolve`
- Role: Staff/Admin
- Headers: `Authorization: Bearer {{staffAccessToken}}`
- Body:
```json
{
  "resolutionSummary": "เก็บขยะและทำความสะอาดเรียบร้อย",
  "resolvedAt": "2026-04-12T21:00:00+07:00"
}
```
- Expected Status Code: `200`

29. **Add Incident Comment**
- Method: `POST`
- URL: `{{baseUrl}}/incidents/{{incidentId}}/comments`
- Role: Staff/Admin
- Headers: `Authorization: Bearer {{staffAccessToken}}`
- Body:
```json
{
  "comment": "รอทีมช่างเข้าพื้นที่"
}
```
- Expected Status Code: `201`

30. **Fusion Explanation**
- Method: `GET`
- URL: `{{baseUrl}}/incidents/{{incidentId}}/fusion-explanation`
- Role: Staff/Admin
- Headers: `Authorization: Bearer {{staffAccessToken}}`
- Expected Status Code: `200`
- Expected Response fields: `matchRules`, `mergedReports`, `explanationText`

31. **Scoring Explanation**
- Method: `GET`
- URL: `{{baseUrl}}/incidents/{{incidentId}}/scoring-explanation`
- Role: Staff/Admin
- Headers: `Authorization: Bearer {{staffAccessToken}}`
- Expected Status Code: `200`
- Expected Response fields: `incidentType`, `severity`, `severityReason`, `confidence`, `confidenceFactors`

### 7.9 Notifications
32. **My Notifications**
- Method: `GET`
- URL: `{{baseUrl}}/notifications/my`
- Role: Staff/Admin
- Headers: `Authorization: Bearer {{staffAccessToken}}`
- Query Params: `page`, `pageSize`, `isRead`
- Expected Status Code: `200`
- Expected Response: paginated notifications

33. **Mark Notification as Read**
- Method: `PATCH`
- URL: `{{baseUrl}}/notifications/{{notificationId}}/read`
- Role: Staff/Admin
- Headers: `Authorization: Bearer {{staffAccessToken}}`
- Expected Status Code: `200`
- Expected Response:
```json
{
  "success": true,
  "message": "อ่านแจ้งเตือนแล้ว",
  "data": {
    "notificationId": "...",
    "isRead": true
  }
}
```

### 7.10 Admin (Master Data)
34. **List Units**
- Method: `GET`
- URL: `{{baseUrl}}/admin/units`
- Role: Admin
- Headers: `Authorization: Bearer {{adminAccessToken}}`
- Query Params: `page`, `pageSize`
- Expected Status Code: `200`

35. **Create Unit**
- Method: `POST`
- URL: `{{baseUrl}}/admin/units`
- Role: Admin
- Headers: `Authorization: Bearer {{adminAccessToken}}`
- Body:
```json
{
  "name": "Facilities",
  "code": "FAC",
  "email": "facilities@tu.ac.th"
}
```
- Expected Status Code: `201`

36. **Create Location**
- Method: `POST`
- URL: `{{baseUrl}}/admin/locations`
- Role: Admin
- Headers: `Authorization: Bearer {{adminAccessToken}}`
- Body:
```json
{
  "locationName": "หน้าตึก LC",
  "lat": 14.072,
  "lng": 100.601,
  "buildingCode": "LC"
}
```
- Expected Status Code: `201`

37. **List Routing Rules**
- Method: `GET`
- URL: `{{baseUrl}}/admin/routing-rules`
- Role: Admin
- Headers: `Authorization: Bearer {{adminAccessToken}}`
- Expected Status Code: `200`

38. **Create Routing Rule**
- Method: `POST`
- URL: `{{baseUrl}}/admin/routing-rules`
- Role: Admin
- Headers: `Authorization: Bearer {{adminAccessToken}}`
- Body:
```json
{
  "incidentType": "fire_smoke",
  "severity": "HIGH",
  "assignedUnitId": "{{unitId}}"
}
```
- Expected Status Code: `201`

39. **Create Staff User**
- Method: `POST`
- URL: `{{baseUrl}}/admin/staff-users`
- Role: Admin
- Headers: `Authorization: Bearer {{adminAccessToken}}`
- Body:
```json
{
  "fullName": "Somying Jaidee",
  "email": "security2@tu.ac.th",
  "password": "Password123!",
  "unitId": "{{unitId}}",
  "role": "STAFF"
}
```
- Expected Status Code: `201`

### 7.11 Analytics
40. **KPI Summary**
- Method: `GET`
- URL: `{{baseUrl}}/analytics/kpi-summary`
- Role: Staff/Admin
- Headers: `Authorization: Bearer {{staffAccessToken}}`
- Query Params: `dateFrom`, `dateTo`, `unitId`
- Expected Status Code: `200`

41. **Incident Type Distribution**
- Method: `GET`
- URL: `{{baseUrl}}/analytics/incident-type-distribution`
- Role: Staff/Admin
- Headers: `Authorization: Bearer {{staffAccessToken}}`
- Query Params: `dateFrom`, `dateTo`
- Expected Status Code: `200`

42. **Hotspot Locations**
- Method: `GET`
- URL: `{{baseUrl}}/analytics/hotspot-locations`
- Role: Staff/Admin
- Headers: `Authorization: Bearer {{staffAccessToken}}`
- Query Params: `dateFrom`, `dateTo`, `limit`
- Expected Status Code: `200`

43. **Peak Time Analysis**
- Method: `GET`
- URL: `{{baseUrl}}/analytics/peak-time-analysis`
- Role: Staff/Admin
- Headers: `Authorization: Bearer {{staffAccessToken}}`
- Query Params: `dateFrom`, `dateTo`, `groupBy` (`hour` หรือ `day`)
- Expected Status Code: `200`
- หมายเหตุ: ถ้า `groupBy` ไม่ใช่ `hour/day` จะได้ `400`

44. **Fusion Statistics**
- Method: `GET`
- URL: `{{baseUrl}}/analytics/fusion-statistics`
- Role: Staff/Admin
- Headers: `Authorization: Bearer {{staffAccessToken}}`
- Query Params: `dateFrom`, `dateTo`
- Expected Status Code: `200`

45. **Status Overview**
- Method: `GET`
- URL: `{{baseUrl}}/analytics/status-overview`
- Role: Staff/Admin
- Headers: `Authorization: Bearer {{staffAccessToken}}`
- Query Params: `dateFrom`, `dateTo`
- Expected Status Code: `200`

## 8. Endpoint ที่ยังไม่พร้อมใช้งานเต็มรูปแบบ
1. `POST /reports/multipart`
- สถานะ: ใช้งานได้ในระดับ prototype
- ติดอะไร: ตอนนี้เก็บไฟล์เป็น URL จำลอง (`/uploads/<filename>`) ยังไม่อัปโหลด object storage จริง
- ต้องทำอะไรต่อ: ต่อ S3/Blob storage + ตรวจไฟล์ (size/mime) แบบ production

2. `GET /analytics/kpi-summary`
- สถานะ: ใช้งานได้
- ติดอะไร: `avgResponseMinutes` ยังเป็น placeholder (`0`) เพราะยังไม่มี event time ที่ใช้คำนวณ response time จริง
- ต้องทำอะไรต่อ: เก็บ timestamp การรับงาน/เริ่มดำเนินการ แล้วคำนวณ metric ใน service

3. Contract บาง error code เฉพาะทางใน API Space
- สถานะ: หลาย endpoint มี status code หลักตรงแล้ว
- ติดอะไร: บางกรณีละเอียด เช่น duplicate fingerprint (`409`), multipart `413/415` ยังไม่มี validation เฉพาะ
- ต้องทำอะไรต่อ: เพิ่ม validation layer และ business rule ตาม spec ที่ละเอียดขึ้น
