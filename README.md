# TU Pulse Backend

Backend ของระบบ TU Pulse / Campus Incident Intelligence Platform (CIIP)

เทคโนโลยีหลัก:
- FastAPI
- PostgreSQL
- SQLAlchemy
- Docker Compose

---

## 1) ภาพรวมโครงสร้างโค้ด

### Root
- [docker-compose.yml](docker-compose.yml): orchestration ของ db + api
- [Dockerfile](Dockerfile): วิธี build image ของ backend
- [requirements.txt](requirements.txt): Python dependencies
- [.env.example](.env.example): ตัวอย่างค่า environment

### App Layer
- [app/main.py](app/main.py): จุดเริ่ม FastAPI, startup lifespan, include router
- [app/api](app/api): endpoint layer และ dependency auth
- [app/services](app/services): business logic
- [app/schemas](app/schemas): request/response models
- [app/models](app/models): database schema (ORM)
- [app/db](app/db): engine/session/base/init
- [app/core](app/core): config, enums, security/JWT

### Flow การเรียกใช้งานหลัก
1. Request เข้า endpoint ใน [app/api/v1/liff_auth.py](app/api/v1/liff_auth.py)
2. Endpoint เรียก service ใน [app/services/auth_service.py](app/services/auth_service.py)
3. Service verify token ผ่าน [app/services/line_service.py](app/services/line_service.py)
4. Service จัดการ DB ผ่าน SQLAlchemy session จาก [app/db/session.py](app/db/session.py)
5. Response กลับผ่าน schema ใน [app/schemas/auth.py](app/schemas/auth.py) และ [app/schemas/common.py](app/schemas/common.py)

---

## 2) โครงสร้างไฟล์สำคัญ (LIFF Auth)

### API Router
- [app/api/v1/router.py](app/api/v1/router.py): รวม v1 routers
- [app/api/v1/liff_auth.py](app/api/v1/liff_auth.py):
	- POST /api/v1/liff/auth/exchange
	- POST /api/v1/liff/auth/refresh
	- POST /api/v1/liff/auth/logout
	- GET /api/v1/liff/auth/me

### Auth Dependency
- [app/api/deps.py](app/api/deps.py)
	- get_current_reporter: ตรวจ Bearer access token และ role ต้องเป็น REPORTER

### Service
- [app/services/line_service.py](app/services/line_service.py)
	- verify_id_token: สลับ mock/real ด้วย LINE_VERIFY_MODE
- [app/services/auth_service.py](app/services/auth_service.py)
	- exchange_liff_token
	- refresh_access_token
	- logout

### Security
- [app/core/security.py](app/core/security.py)
	- create_access_token
	- create_refresh_token
	- decode_access_token
	- decode_refresh_token
	- hash_token

### Database Models (Auth)
- [app/models/user.py](app/models/user.py): ตาราง users
- [app/models/refresh_token.py](app/models/refresh_token.py): ตาราง refresh_tokens

---

## 3) ก่อนรันต้องมีอะไรติดตั้ง

1. Docker Desktop (Windows/Mac) หรือ Docker Engine + Compose plugin (Linux)
2. Git
3. (แนะนำ) Postman สำหรับทดสอบ API

ตรวจเวอร์ชัน:

```bash
docker --version
docker compose version
```

---

## 4) วิธีรันโปรเจกต์ด้วย Docker Compose (ทีละขั้น)

### Step 1: เตรียมไฟล์ env

คัดลอกไฟล์ตัวอย่าง:

```bash
cp .env.example .env
```

ถ้าใช้ PowerShell:

```powershell
Copy-Item .env.example .env
```

ค่าแนะนำสำหรับการรันผ่าน compose:
- POSTGRES_HOST=db
- POSTGRES_PORT=5432
- POSTGRES_EXPOSE_PORT=5435
- DATABASE_URL=postgresql+psycopg2://postgres:postgres@db:5432/tu_pulse
- LINE_VERIFY_MODE=mock

หมายเหตุ:
- POSTGRES_PORT = พอร์ตภายใน network ของ compose
- POSTGRES_EXPOSE_PORT = พอร์ตฝั่งเครื่อง host สำหรับต่อจากภายนอก

### Step 2: Build และ Start

```bash
docker compose up --build -d
```

### Step 3: เช็กสถานะ

```bash
docker compose ps
```

### Step 4: ดู log

```bash
docker compose logs -f db
docker compose logs -f api
```

### Step 5: เช็กว่า API พร้อม

เปิด:
- http://localhost:8000/
- http://localhost:8000/docs

ถ้าได้ response จาก root endpoint และเปิด Swagger ได้ แปลว่ารันสำเร็จ

---

## 5) วิธีทดสอบ API ด้วย Postman (ละเอียด)

Base URL:

```text
http://localhost:8000/api/v1/liff/auth
```

### 5.0 ตัวอย่าง response ที่คาดหวัง

ตัวอย่าง response สำหรับแต่ละ endpoint ของ LIFF Auth:

#### POST /exchange

```json
{
	"success": true,
	"message": "เข้าสู่ระบบผ่าน LINE สำเร็จ",
	"data": {
		"accessToken": "...",
		"refreshToken": "...",
		"user": {
			"userId": "usr_001",
			"lineUserId": "U123",
			"fullName": "Arm",
			"role": "REPORTER"
		}
	}
}
```

#### POST /refresh

```json
{
	"success": true,
	"message": "ต่ออายุ token สำเร็จ",
	"data": {
		"accessToken": "..."
	}
}
```

#### POST /logout

```json
{
	"success": true,
	"message": "ออกจากระบบสำเร็จ",
	"data": null
}
```

#### GET /me

```json
{
	"success": true,
	"message": "ดึงข้อมูลผู้ใช้สำเร็จ",
	"data": {
		"userId": "usr_001",
		"fullName": "Arm",
		"lineDisplayName": "Arm",
		"role": "REPORTER",
		"reporterType": "STUDENT"
	}
}
```

### 5.1 POST exchange

URL:

```text
POST {{baseUrl}}/exchange
```

Headers:
- Content-Type: application/json

Body (raw JSON):

```json
{
	"idToken": "mock-line-token-student001",
	"displayName": "Student 001",
	"pictureUrl": "https://example.com/me.jpg"
}
```

Expected response:
- success = true
- data.accessToken
- data.refreshToken
- data.user.userId

Error ที่อาจเจอ:
- 401 Line token invalid
- 400 Invalid token payload

หลังจากยิงสำเร็จ ให้เก็บค่า:
- accessToken
- refreshToken

### 5.2 POST refresh

URL:

```text
POST {{baseUrl}}/refresh
```

Headers:
- Content-Type: application/json

Body:

```json
{
	"refreshToken": "{{refreshToken}}"
}
```

Expected response:
- success = true
- data.accessToken (ตัวใหม่)

Error ที่อาจเจอ:
- 401 Invalid refresh token
- 401 Refresh token expired
- 403 Refresh token revoked

### 5.3 GET me

URL:

```text
GET {{baseUrl}}/me
```

Headers:
- Authorization: Bearer {{accessToken}}

Expected response:
- success = true
- data.userId, fullName, lineDisplayName, role, reporterType

Error ที่อาจเจอ:
- 401 Invalid access token
- 401 User not found or inactive
- 403 Only reporter can access this endpoint

### 5.4 POST logout

URL:

```text
POST {{baseUrl}}/logout
```

Headers:
- Content-Type: application/json

Body:

```json
{
	"refreshToken": "{{refreshToken}}"
}
```

Expected response:
- success = true
- data = null

ทดสอบซ้ำหลัง logout:
1. เรียก /refresh ด้วย refreshToken เดิม
2. ควรเจอ 403 Refresh token revoked

---

## 6) แนะนำการตั้งค่า Postman Environment

สร้าง environment variables:
- baseUrl = http://localhost:8000/api/v1/liff/auth
- accessToken = (เว้นว่าง)
- refreshToken = (เว้นว่าง)

หลังยิง exchange สำเร็จ ให้อัปเดตค่าจาก response

ตัวอย่าง Tests script ใน Postman (สำหรับ request exchange):

```javascript
pm.test('exchange success', function () {
	pm.response.to.have.status(200);
	const body = pm.response.json();
	pm.expect(body.success).to.eql(true);
	pm.environment.set('accessToken', body.data.accessToken);
	pm.environment.set('refreshToken', body.data.refreshToken);
});
```

ตัวอย่าง Tests script ใน request refresh (overwrite accessToken):

```javascript
pm.test('refresh success', function () {
	pm.response.to.have.status(200);
	const body = pm.response.json();
	pm.expect(body.success).to.eql(true);
	pm.environment.set('accessToken', body.data.accessToken);
});
```

---

## 7) Mock LINE Token คืออะไร

กำหนดที่ [app/services/line_service.py](app/services/line_service.py)

เมื่อ LINE_VERIFY_MODE=mock:
1. backend จะไม่ยิงไป LINE จริง
2. idToken ต้องขึ้นต้นด้วย mock-line-token-
3. ตัวอย่าง token ที่ใช้ทดสอบได้ทันที: mock-line-token-student001

เมื่อ LINE_VERIFY_MODE ไม่ใช่ mock:
1. backend จะเรียก LINE verify endpoint จริง
2. ต้องกำหนด LINE_CHANNEL_ID ให้ถูกต้อง

---

## 8) สรุปตาราง Auth ที่สำคัญ

### users
- เก็บผู้ใช้ทุกประเภท
- รองรับหลายช่องทาง auth ด้วย auth_provider
- reporter (LIFF) ใช้ line_user_id
- staff/admin (อนาคต) ใช้ email/password_hash ได้

### refresh_tokens
- เก็บ hash ของ refresh token
- มี expires_at และ revoked_at
- ใช้ revoke token ตอน logout ได้แบบปลอดภัย

---

## 9) คำสั่งที่ใช้บ่อย

เริ่มระบบ:

```bash
docker compose up --build -d
```

หยุดระบบ:

```bash
docker compose down
```

หยุดและลบ volume db:

```bash
docker compose down -v
```

ดู log:

```bash
docker compose logs -f api
docker compose logs -f db
```
