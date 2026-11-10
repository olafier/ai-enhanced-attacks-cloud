# การโจมตีโครงสร้างพื้นฐานคลาวด์ที่เสริมด้วย AI

*[English](README.md) · ภาษาไทย*

งานทบทวนวรรณกรรมและข้อเสนอการวิจัยว่า AI กำลังเปลี่ยน **ความเร็ว** และ **พื้นที่โจมตีด้านตัวตน (identity attack surface)** ของสภาพแวดล้อมคลาวด์อย่างไร — พร้อมการทดลองแบบมีการควบคุมเพื่อวัดผลกระทบจำเพาะอย่างหนึ่งของการเปลี่ยนแปลงนั้น

**สถานะ:** ทบทวนวรรณกรรมเสร็จ · นำเสนอที่ UTCC สิงหาคม 2026 · **Phase 1 มีผลชุดแรกแล้ว** (วัดระดับขอบเขตสิทธิ์) · การทดลองเชิงพฤติกรรมด้วย CloudTrail ยังไม่ได้รัน

**ผู้จัดทำ:** จารุเดช ทองคำ — วิทยาการคอมพิวเตอร์ มหาวิทยาลัยหอการค้าไทย

**สไลด์:** [ดูการนำเสนอบน Canva](https://canva.link/xcb7ndjorsurisj)

**Lab ของ Phase 1:** [olafier/iam-blast-radius-lab](https://github.com/olafier/iam-blast-radius-lab)

---

## ปัญหา

รายงานอุตสาหกรรมปี 2026 สี่ฉบับที่เป็นอิสระต่อกัน ชี้ไปทางเดียวกัน: ผู้โจมตีไม่ได้คิดเทคนิคใหม่ แต่ลงมือเทคนิคเดิม **ได้เร็วขึ้น** และสิ่งที่พวกเขาโจมตีได้ผลที่สุดคือ **ตัวตน (identity)**

| แหล่งข้อมูล | สิ่งที่รายงาน |
|---|---|
| CSA — Top Threats to Cloud Computing 2026 | *AI-Enhanced Attacks* เข้ามาอันดับ **#2**; *Inadequate IAM* อยู่อันดับ **#1**; misconfiguration ร่วงจาก #1 ไป #5 |
| Google Cloud — Threat Horizons H1 2026 | การเจาะผ่านช่องโหว่ซอฟต์แวร์เพิ่มจาก **2.9% → 44.5%** ของการเข้าถึงครั้งแรก; การถูกเจาะผ่าน third-party เกี่ยวข้อง **21%** ของเคส |
| Verizon — DBIR 2026 | การเจาะช่องโหว่แซงการขโมย credential ขึ้นเป็นช่องทางอันดับหนึ่ง (**≈31%**); third-party เกี่ยวข้อง **48%** เพิ่มขึ้น **60%** เทียบปีก่อน |
| OWASP — GenAI Top 10 2026 | *Excessive Agency* อันดับสูงขึ้น — ระบบ AI ถูกให้สิทธิ์เกินกว่างานต้องการ |

ชุดข้อมูลสองชุดที่เก็บจากประชากรคนละกลุ่มกันโดยสิ้นเชิง กลับชี้ไปทางเดียวกัน ความสอดคล้องนี้เองคือข้อค้นพบ

---

## กรณีศึกษา — UNC6426

Google Cloud บันทึกการบุกรุกครั้งเดียวที่ย่อข้อโต้แย้งทั้งหมดไว้ใน **เวลาไม่ถึง 72 ชั่วโมง** ทุกขั้นด้านล่างอ้างอิงหรือสรุปจากรายงานโดยตรง

```
วันที่ 1  แพ็กเกจ Nx npm ถูกเจาะ → นักพัฒนาติดตั้งอัปเดต → โค้ดอันตรายทำงาน
         QUIETVAULT เก็บเกี่ยว GitHub + NPM API keys
         ↳ "ใช้ AI ช่วยระบุไฟล์ที่น่าสนใจ"   ← ขั้นตอนเดียวที่ใช้ AI
         อัปโหลด keys ขึ้น public GitHub repository

วันที่ 3  ผู้โจมตีใช้ key ที่ขโมยมาเข้า GitHub แล้วสำรวจสภาพแวดล้อม
         ใช้ประโยชน์จากความสัมพันธ์ GitHub-to-AWS OIDC trust
         ↳ สร้าง AWS STS token ชั่วคราวให้ role Github-Actions-CloudFormation

วันที่ 4  "role Github-Actions-CloudFormation ที่ถูกเจาะมีสิทธิ์มากเกินไป"
         deploy CloudFormation stack ที่มีจุดประสงค์เดียวคือสร้าง IAM role
         ที่แนบ AdministratorAccess
         ดึงข้อมูล S3, terminate EC2 และ RDS โปรดักชัน, ถอดรหัส application key
```

**ไม่มี zero-day ไม่มีเทคนิคใหม่** AI ทำเพียงขั้นตอนเดียวตรงกลาง — ส่วนที่เมื่อก่อนมนุษย์ทำด้วยมือ

ประโยคที่สำคัญที่สุดต่อสิ่งที่ตามมา คือประโยคที่ Google เขียนตรง ๆ ว่า: *role นั้นมีสิทธิ์มากเกินไป*

---

## การทดลอง

### คำถามวิจัย

> **ขอบเขตสิทธิ์ IAM ส่งผลต่อ blast radius ของตัวตนคลาวด์ที่ถูกเจาะอย่างไร?**

จงใจ *ไม่* ตั้งว่า "least privilege ได้ผลไหม" — คำถามนั้นมีคำตอบอยู่แล้วและไม่ให้ข้อมูล ส่วนคำถามนี้ให้ตัวเลข

### วิธีการ

ตัวตนที่ถูกเจาะหนึ่งตัว · **ชุด action คงที่** ครอบ read, write, destroy, escalate · นโยบาย IAM สามแบบ ไม่มีอะไรเปลี่ยนนอกจากนโยบาย

MVP วางไว้ 15 action บน S3 + EC2 ส่วน Phase 1 ที่รันจริง **ขยายเป็น 100 action ครอบ 12 บริการ** (S3, EC2, IAM, STS, Lambda, DynamoDB, KMS, CloudTrail, CloudWatch Logs, Secrets Manager, SSM, RDS) จัดหมวด READ 41 · WRITE 26 · DESTROY 20 · ESCALATE 13

### เครื่องมือสองชนิด สองประเภทของข้ออ้าง

วิธีการแยกระหว่าง **นโยบายอนุญาตอะไร** กับ **เกิดอะไรขึ้นจริงเมื่อลงมือเรียก action** สองอย่างนี้ต้องใช้เครื่องมือต่างกัน และ Phase 1 รายงานเพียงอย่างแรก

- **ระดับขอบเขตสิทธิ์ — `iam:SimulateCustomPolicy` (ทำแล้ว)** ถาม AWS ว่าแต่ละ action อนุญาตไหม โดยไม่เรียกจริงและไม่สร้างอะไร เป็นการวัดขอบเขตที่สะอาดและปลอดภัย
- **เชิงพฤติกรรม — CloudTrail (ยังไม่ทำ)** เรียก action จริงแล้วนับ `eventName` + `errorCode` จาก log นี่คือการทดลองเชิงพฤติกรรมที่ roadmap มุ่งไป จนกว่าจะรัน ตัวเลขด้านล่างยังเป็นระดับสิทธิ์ ไม่ใช่เชิงพฤติกรรม

```
policy A   eventName TerminateInstances   errorCode —              → ทำได้
policy C   eventName TerminateInstances   errorCode AccessDenied   → ถูกบล็อก
policy A   eventName CreateRole           errorCode AccessDenied   → ถูกบล็อก (IAM mutation)
```

ถ้าไม่มี log ก็ไม่มีการทดลองเชิงพฤติกรรม — มีแค่การวัดสิทธิ์ Phase 1 ซื่อตรงว่าเป็นอย่างหลัง

### ผล — ระดับขอบเขตสิทธิ์ (IAM Policy Simulator, 100 action)

ข้อมูลเต็ม กราฟ และการรันบน CloudShell อยู่ใน [`/lab`](lab) และที่ [iam-blast-radius-lab](https://github.com/olafier/iam-blast-radius-lab)

| | Policy A — over-permissive | Policy B — moderate | Policy C — least privilege |
|---|---|---|---|
| Action ที่อนุญาต | **91 / 100** | **43 / 100** | **6 / 100** |
| Action Success Rate | 91.0% | 43.0% | 6.0% |
| Weighted Blast Radius | 83.9% | 25.9% | 3.9% |
| ทำ action ทำลายได้ไหม? | **ได้ (19/20)** | ไม่ได้ (0/20) | ไม่ได้ (0/20) |
| ยกระดับเป็น administrator ได้ไหม? | **บางส่วน (6/13)** | ไม่ได้ (0/13) | ไม่ได้ (0/13) |

**ช่องที่ข้อเสนอเดิมเว้นว่าง ถูกเติมแล้ว — ที่ระดับสิทธิ์** การทดลองเชิงพฤติกรรมด้วย CloudTrail จะเติมใหม่ด้วยจำนวนที่เรียกจริงและถูกบันทึก

สองเมตริก กำหนดน้ำหนักก่อนรัน:

- **ASR** = อนุญาต / ทั้งหมด × 100 — ทุก action นับเท่ากัน
- **WBR** = Σ น้ำหนัก(อนุญาต) / Σ น้ำหนัก(ทั้งหมด) × 100 โดย READ 1 · WRITE 2 · DESTROY 3 · ESCALATE 4 — นับตามความรุนแรง

สามข้อค้นพบ:

1. **Blast radius โตแบบไม่เป็นเส้นตรงตามขอบเขต** least privilege → moderate เพิ่ม ASR 37 จุด แต่ WBR แค่ 22 จุด (moderate ได้แค่ READ/WRITE) ; moderate → over-permissive เพิ่ม WBR 58 จุด เพราะ DESTROY และ ESCALATE เปิด
2. **ช่องว่าง ASR − WBR สะท้อนความรุนแรง** moderate ทำ action ได้ 43% แต่น้ำหนักแค่ 25.9% เพราะไม่มี action ทำลาย ส่วน over-permissive ช่องว่างแคบลง (91 เทียบ 83.9)
3. **"ไม่มี `iam:*`" ≠ "ยกระดับสิทธิ์ไม่ได้"** นโยบาย over-permissive ถูกปฏิเสธ action แก้ไข IAM identity ทั้ง 9 ตัว แต่ยังทำ ESCALATE ได้ 6 จาก 13 ผ่าน resource policy และ execution path (`s3:PutBucketPolicy`, `kms:PutKeyPolicy`, `secretsmanager:PutResourcePolicy`, `ec2:AssociateIamInstanceProfile`, `sts:AssumeRole`, `ssm:SendCommand`) นี่คือกลไกเบื้องหลัง role ที่ "มีสิทธิ์มากเกินไป" ของ UNC6426

### ขอบเขต

**MVP:** นโยบาย IAM · ชุด action คงที่ · การวัดระดับขอบเขตสิทธิ์ — **ทำแล้ว**

**ถัดไป:** การทดลองเชิงพฤติกรรมด้วย CloudTrail · OIDC trust · CI/CD identity · การตรวจจับอัตโนมัติ · การตอบสนองอัตโนมัติ

---

## Roadmap

| Phase | โฟกัส | สถานะ |
|---|---|---|
| **1** | IAM blast-radius — วัดขอบเขตสิทธิ์เทียบชุด action คงที่ | **ระดับสิทธิ์เสร็จ**; เชิงพฤติกรรม (CloudTrail) ยังรอ |
| **2** | OIDC / CI-CD identity — ขยับ setup เข้าใกล้ chain จริงของ UNC6426 | ยังไม่เริ่ม |
| **3** | การตรวจจับและตอบสนองอัตโนมัติ — กิจกรรมนี้ตรวจจับและจำกัดได้ไหม? | ยังไม่เริ่ม |
| **อนาคต** | ใช้ AI ช่วยวิเคราะห์ log เพื่อเร่งการสืบสวน | ยังไม่เริ่ม |

---

## เนื้อหาใน repository

```
/slides       สไลด์นำเสนอ (PDF)
/notes        บันทึกการอ่านแยกตามแหล่ง
/sources.md   ทุกตัวเลขโยงไปรายงานต้นทาง
/lab          การทดลอง Phase 1 — นโยบาย IAM, ชุด action, สคริปต์, ผล, หลักฐานการรัน
```

Lab ของ Phase 1 เผยแพร่แบบ standalone ด้วยที่
[olafier/iam-blast-radius-lab](https://github.com/olafier/iam-blast-radius-lab) ส่วนสำเนาใน
[`/lab`](lab) เก็บให้ตรงกัน

---

## แหล่งข้อมูล

- [Cloud Security Alliance — Top Threats to Cloud Computing 2026](https://cloudsecurityalliance.org/artifacts/top-threats-cloud-computing-2026)
- [Google Cloud — Cloud Threat Horizons Report H1 2026](https://cloud.google.com/security/report/resources/cloud-threat-horizons-report-h1-2026)
- [Verizon — 2026 Data Breach Investigations Report](https://www.verizon.com/business/resources/reports/dbir/)
- [OWASP GenAI Security Project — Top 10 for LLM Applications 2026](https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/)

---

## หมายเหตุเรื่องความซื่อตรง

ตัวเลขบนสไลด์โยงไปแหล่งที่ระบุชื่อ ที่ใดตัวเลขมาจากการรายงานทุติยภูมิแทนรายงานต้นฉบับ จะบันทึกไว้ใน `sources.md`

Phase 1 มีผลชุดแรกแล้ว และ repository นี้ระบุชัดว่าเป็นผลชนิดใด: เป็น **การวัดระดับขอบเขตสิทธิ์** จาก IAM Policy Simulator ซึ่ง "allowed" แปลว่า *นโยบายอนุญาต* ไม่ใช่ *เรียกจริงและถูกบันทึก* ส่วน **การทดลองเชิงพฤติกรรมที่ใช้ CloudTrail เป็นเครื่องมือยังไม่ได้รัน** และไม่มีตัวเลขจาก simulator ตัวใดถูกนำเสนอเป็นผลเชิงพฤติกรรม นอกจากนี้ simulator เห็นเฉพาะ identity policy — ไม่รวม SCP, permission boundary, resource policy ฝั่งเป้าหมาย หรือ trust policy ของ role
