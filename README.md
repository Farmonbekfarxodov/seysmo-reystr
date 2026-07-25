# Seysmologiya instituti — xodimlar reyestri

Seysmologiya instituti (O'zbekiston) uchun ochiq xodimlar reyestri. Har kim
hisobsiz xodimlar profilini qidirib, ko'rishi mumkin. Faqat xodimlar
ro'yxatdan o'tadi (email tasdiqlash orqali); tasdiqlangandan so'ng profil
darhol va doimiy ravishda ochiq bo'ladi — hech qanday admin tasdiqlash
bosqichi va ko'rinish/yashirish tugmasi yo'q.

- **Backend:** Django 6 + DRF, JWT autentifikatsiya (`djangorestframework-simplejwt`), PostgreSQL, Pillow, openpyxl, zipstream-ng
- **Frontend:** React 18 (Vite), React Router, Axios, **Tailwind CSS v4**, sessiya holati uchun React Context
- **Interfeys tili:** O'zbek tili (`frontend/src/i18n/uz.js`)

```
seismology-staff-registry/
├── docker-compose.yml
├── backend/     Django loyihasi (API)
└── frontend/    React ilovasi (Vite)
```

## Qabul qilingan qarorlar

- Kirish (login) maydoni **foydalanuvchi nomi YOKI email**ni bitta maydonda qabul qiladi.
- **Admin tasdiqlash jarayoni yo'q.** Loyihaning oldingi versiyalarida
  kutilmoqda/tasdiqlangan/rad etilgan degan moderatsiya bosqichi bor edi;
  bu butunlay olib tashlangan. Tasdiqlangan, faol hisobning profili
  har doim ochiq — yagona shart email tasdiqlanishi.
  - `is_public`, `moderation_status` va `rejection_reason` **ustunlari
    bazada hali ham mavjud** (migratsiyadan qochish uchun saqlab
    qolingan), lekin ilova ularni hech qayerda o'qimaydi yoki yozmaydi.
    Bular amalda "o'lik" ustunlar.
  - Django admin panelida `SpecialistProfile` uchun tasdiqlash/rad etish
    amallari yoki moderatsiyaga oid filtr/maydonlar endi yo'q.
- **Bo'lim (department)** — haqiqiy tanlov ro'yxati (dropdown), admin
  tomonidan boshqariladi, erkin matn emas.
- `research_interests` (ilmiy qiziqishlar) ro'yxatdan o'tishda so'raladi;
  `bio` (qisqacha ma'lumot) faqat shaxsiy kabinetda to'ldiriladi.
- **Ilmiy ishlar eski, oddiy hujjatlar ro'yxati o'rnini bosadi.** Har bir
  xodimning nashrlari bitta `ScientificWork` jadvalida, oltita kategoriya
  bo'yicha saqlanadi (xorijiy maqolalar, mahalliy maqolalar, tezislar,
  anjumanda ishtirok, patentlar, boshqa nashrlar), har birining o'z
  majburiy/ixtiyoriy maydonlari bilan. PDF fayli **anjumanda ishtirokdan
  tashqari har bir kategoriyaning har bir yozuvida majburiy** (sertifikat
  keyinroq ham kelishi mumkin), yuklash **faqat shaxsiy kabinetdan**
  (ro'yxatdan o'tishda hech qachon emas) amalga oshiriladi, va profil
  ochiq bo'lgach (ya'ni hisob tasdiqlangach), shu xodimning barcha
  ishlari — jumladan PDF yuklab olish havolalari — ham ochiq bo'ladi.
  Bu ataylab asl "hujjatlarni hech qachon ochiq qilmaslik" g'oyasini
  bekor qiladi, chunki bu fayllar shunchaki tekshirish uchun
  hujjatlar emas, balki ochiq topilishi kerak bo'lgan ilmiy ishlardir.
  - **Eski `SpecialistDocument` yozuvlari ko'chirildi**, o'chirilmadi:
    har biri `local_article`ga aylandi, `title` = asl fayl nomi
    (kengaytmasiz) va `year` = yuklangan yil sifatida — ikkalasi ham
    keyinchalik tahrirlanishi mumkin. Qarang:
    `specialists/migrations/0003_migrate_documents_to_works.py`.
  - **Faylni faqat almashtirish mumkin, o'chirib bo'lmaydi**: `PATCH`
    PDF'ni almashtira oladi, lekin ish hech qachon fayilsiz qolib
    ketmaydi (anjumanda ishtirokdan tashqari — u fayilsiz boshlanishi
    mumkin).
  - **DOI takrorlanishi** — qattiq to'siq emas, balki yumshoq, tasdiqlash
    talab qiluvchi ogohlantirish, har bir xodim doirasida — ikki xil
    xodim bitta DOI'ni bemalol baham ko'rishi mumkin.
  - **PDF tekshiruvi** endi haqiqiy `%PDF-` magic-byte tekshiruvini
    o'z ichiga oladi (qo'shimcha kutubxonasiz), bu `.docx` fayl nomi
    `.pdf`ga o'zgartirilgan holatni ham aniqlaydi.
  - Qo'shimcha ixtiyoriy imkoniyatlar amalga oshirildi: dashboard'dagi
    ishlar bo'limi tepasida **har bir kategoriya bo'yicha qisqacha
    umumiy son**, va **loyiha nomi uchun avtomatik taklif** (datalist,
    xodimning o'zi avval kiritgan nomlardan).
- **Rasmiy yillik hisobot moduli**: har bir `ScientificWork` yozuvi
  kategoriyaga xos klassifikatsiya maydonlaridan hisoblab chiqilgan
  `report_code` (masalan, `2.1`, `3.4.2`, `6.3`) ni olib yuradi,
  `python manage.py recalc_report_codes` orqali qayta hisoblanadi.
  Asosiy qarorlar:
  - **Institut bo'yicha admin hisoboti = JWT bilan himoyalangan,
    faqat `staff` huquqiga ega foydalanuvchilar uchun endpoint**
    (`/api/reports/institute/`), maxsus Django admin sahifasi emas.
  - **Har bir xodim bo'yicha taqsimot jadvali xodimning o'z (birlashtirilmagan)
    sonlarini ko'rsatadi**; faqat institutning umumiy jami ko'rsatkichlari
    birlashtiriladi (normallashtirilgan DOI bo'yicha, DOI bo'lmasa —
    kategoriya+nom+yil signaturasi bo'yicha). Ikki xodim bir xil ishni
    ro'yxatdan o'tkazsa, ikkalasi ham buni o'z shaxsiy hisobotida ko'radi.
  - **Laboratoriya bo'yicha taqsimot**: har bir birlashtirilgan guruh
    o'zining vakil yozuvi bo'limiga tegishli deb hisoblanadi, shunda
    bo'lim raqamlari institut jamisiga aniq mos keladi.
  - **Taksonomiya migratsiyasi hech qachon taxmin qilmaydi**: eski
    ma'lumot yangi rasmiy kategoriyalarga aniq mos kelmasa, yozuv
    klassifikatsiyalanmagan (`report_code=""`) deb qoldiriladi va
    hisobotning ogohlantirish bannerida ko'rsatiladi — bu har bir holat
    uchun simulyatsiya qilingan eski ma'lumotlar asosida tekshirilgan.
- **Hisobot bo'yicha batafsil ko'rish va ZIP eksporti**: ikkala hisobot
  ko'rinishida ham har qanday noldan farqli son (har bir band, har bir
  kvartil katagi, har bir bo'lim "Jami"si) bosiladigan bo'ladi va aniq
  shu sonni tashkil etgan yozuvlar ro'yxatini ko'rsatuvchi oyna ochadi —
  bu xuddi umumiy sonni hisoblashda ishlatilgan funksiyaning o'zi
  (`resolve_line_records()`) orqali amalga oshiriladi, shuning uchun
  oynadagi qatorlar soni hisobotdagi ko'rsatkichdan hech qachon
  farq qilmaydi (bu tenglik shunchaki taxmin qilinmagan, balki
  testlarda to'g'ridan-to'g'ri tekshirilgan).
  - **Institut oynasi hammuallif bo'lgan ish uchun bitta birlashtirilgan
    qator ko'rsatadi**, institutdagi barcha hammualliflarni sanab
    o'tadi (asosiy muallif belgilangan holda); **shaxsiy hisobot oynasi
    hech qachon birlashtirilmaydi** va muallif ustunini ko'rsatmaydi,
    chunki har bir qator allaqachon xodimning o'ziniki.
  - Egalik huquqi / faqat-xodim tekshiruvlari ro'yxat va ZIP
    endpointlarining ikkalasida ham API darajasida amalga oshirilgan,
    shunchaki interfeysda yashirilmagan — testlar xodim boshqa birovning
    yozuvlariga yeta olmasligini va faqat-xodim bo'lmagan foydalanuvchi
    har qanday institut endpointidan rad etilishini tasdiqlaydi.
  - ZIP fayllar **`zipstream-ng`** yordamida haqiqiy generator asosidagi
    oqim sifatida quriladi (har bir fayl 64KB qismlarda o'qilib,
    birma-bir ochilib-yopiladi), butun arxivni xotirada yoki diskda
    to'liq yig'ish o'rniga — so'rovda aytilganidek. Har bir ZIP
    `_haqida.txt` manifest faylini o'z ichiga oladi va sertifikatsiz
    yozuvlarni eslatma bilan o'tkazib yuboradi.
- Qo'shimcha ixtiyoriy imkoniyat amalga oshirildi: **`ALLOWED_EMAIL_DOMAIN`**
  (ro'yxatdan o'tishni korporativ domen bilan cheklash). Amalga
  oshirilmagan (quyida kelajakdagi ishlar sifatida ko'rsatilgan):
  ORCID/Scholar/Scopus + nashrlar ro'yxati, "Bo'limlar" ko'rish sahifasi,
  va til almashtirgich.
- **Holat boshqaruvi: React Context**, Redux Toolkit emas — umumiy holat
  (sessiya + qaysi oyna ochiq ekani) shu miqyosda hech narsani
  yo'qotmasdan qo'shimcha kutubxona og'irligini talab qilmaydigan
  darajada kichik.
- **Tailwind CSS v4** (joriy barqaror versiya) — `frontend/src/styles/index.css`
  faylida `@theme` orqali CSS-birinchi konfiguratsiya, `@tailwindcss/vite`
  plagini yordamida. `tailwind.config.js` / `postcss.config.js` kerak emas.

## Dizayn rejasi

- **Palitra:** `ink` #0F2A43 (sarlavhalar/matn), `ink-soft` #4B5C72, `sand`
  #B8863A (urg'u/tugmalar), `sand-dark` #8E6526 (hover holati), `paper`
  #FAFAF8 (fon), `surface` #FFFFFF (kartochkalar), shuningdek ogohlantirishlar
  uchun `success`/`warning`/`danger`.
- **Shrift:** **Fraunces** (displey serif, faqat hero va bo'lim sarlavhalari
  uchun), **Inter** bilan birga (matn/interfeys). 8px oralig'i ritmi.
- **Imzo elementi:** hero sarlavhasi ostida va footer ustida statik SVG
  **seysmogramma to'lqini** izi (`components/Seismogram.jsx`), yuklanishda
  yengil chizib-chiqish animatsiyasi bilan (`prefers-reduced-motion`
  yoqilganda o'chiriladi). Qolgan hamma narsa jim va intizomli holda qoladi.

---

## A-variant — Docker bilan ishga tushirish (tavsiya etiladi)

```bash
git clone <this-repo>
cd seismology-staff-registry
docker compose up --build
```

Bu PostgreSQL'ni (`localhost:5432`), Django backend'ni
(`http://localhost:8000`, migratsiyalar avtomatik ishga tushadi) va React
frontend'ni (`http://localhost:5173`) ishga tushiradi.

Ikkinchi terminalda admin yarating va boshlang'ich ma'lumotlarni yuklang:

```bash
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py seed_data
```

`http://localhost:5173` sahifasini oching.

## B-variant — Docker'siz ishga tushirish

### Talablar
Python 3.11+, Node.js 18+, lokal ishlayotgan PostgreSQL 14+.

### 1. Bazani yaratish

```bash
psql -U postgres
```
```sql
CREATE DATABASE seismology_registry;
CREATE USER seismology_registry WITH PASSWORD 'seismology_registry';
GRANT ALL PRIVILEGES ON DATABASE seismology_registry TO seismology_registry;
ALTER DATABASE seismology_registry OWNER TO seismology_registry;
```

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# DB ma'lumotlaringiz boshqacha bo'lsa, .env faylini tahrirlang

python manage.py migrate
python manage.py createsuperuser
python manage.py seed_data                    # bo'limlar (demo xodimlarsiz)

python manage.py runserver                     # http://localhost:8000
```

Django admin: `http://localhost:8000/admin/`.

### 3. Frontend

```bash
cd frontend
npm install

cp .env.example .env
# backend http://localhost:8000 da bo'lmasa, .env faylini tahrirlang

npm run dev                                     # http://localhost:5173
```

---

## Muhit o'zgaruvchilari

### `backend/.env`

| O'zgaruvchi | Standart qiymat | Izoh |
|---|---|---|
| `DEBUG` | `True` | |
| `SECRET_KEY` | — | dev muhitidan tashqarida haqiqiy tasodifiy qiymat qo'ying |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | vergul bilan ajratilgan |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` / `DB_HOST` / `DB_PORT` | `seismology_registry` / … / `5432` | |
| `FRONTEND_ORIGIN` | `http://localhost:5173` | CORS ruxsat ro'yxati |
| `EMAIL_BACKEND` | console backend | haqiqiy email uchun SMTP'ga almashtiring |
| `EMAIL_HOST` / `EMAIL_PORT` / `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` / `EMAIL_USE_TLS` | — | SMTP sozlamalari (production uchun) |
| `DEFAULT_FROM_EMAIL` | `no-reply@seismology-institute.local` | |
| `ACCESS_TOKEN_LIFETIME_MINUTES` | `15` | |
| `REFRESH_TOKEN_LIFETIME_DAYS` | `7` | |
| `ALLOWED_EMAIL_DOMAIN` | *(bo'sh = istalgan domen)* | masalan `seismology.uz` — ro'yxatdan o'tishni cheklash uchun |

### `frontend/.env`

| O'zgaruvchi | Standart qiymat |
|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8000/api` |

## Mavjud joylashtirishni yangilash

Agar sizda eski, oddiy hujjatlar ro'yxati tizimida hujjat yuklagan
xodimlar bilan allaqachon ishlayotgan nusxa bo'lsa, yangilash oddiy
migratsiyadan iborat — **qo'lda hech qanday ma'lumot bilan ishlash
shart emas**:

```bash
git pull
docker compose up -d --build      # yoki: python manage.py migrate  (Docker'siz)
```

`python manage.py migrate` (yoki `docker compose up -d --build`) ishga
tushirilganda barcha migratsiyalar avtomatik, tartib bilan qo'llaniladi —
jumladan branch+merge (ikkita migratsiya bir xil ajdoddan yaratilgan edi —
biri Bakalavr/Magistr darajalarini qo'shgan, biri ilmiy ishlar jadvalini
qo'shgan — va merge migratsiyasi ularni birlashtiradi) hamda eski
klassifikatsiya maydonlarini yangi rasmiy hisobot taksonomiyasiga
ko'chiruvchi, `monograph`ni `other_publication`ga qayta nomlaydigan
hisobot-taksonomiyasi ketma-ketligi (`0006`→`0008`). **Eski ma'lumot yangi
rasmiy kategoriyalarga aniq mos kelmasa** (masalan eski "Sanoat namunasi"
patenti, yoki xorijiy dasturiy ta'minot guvohnomasi), yozuv taxmin
qilinmasdan klassifikatsiyalanmagan holda qoldiriladi — u shu xodimning
"Hisobot" ogohlantirish bannerida ko'rinadi. Bu ham, asl
hujjatlar→ishlar migratsiyasi ham, chiqarilishdan oldin simulyatsiya
qilingan production ma'lumotlariga (har bir moslashtirish holatini
qamrab olgan holda) qarshi sinovdan o'tkazilgan.

Agar sizda juda katta `ScientificWork` jadvali bo'lsa va yangilanishdan
so'ng hamma narsa kutilganidek klassifikatsiyalanganini tekshirib
ko'rmoqchi bo'lsangiz, shuni ishga tushiring:

```bash
python manage.py recalc_report_codes
```

Bu — idempotent (necha marta ishga tushirilsa ham natija bir xil) va
istalgan vaqtda xavfsiz ishga tushirsa bo'ladi.

## Email tasdiqlash rivojlantirish muhitida qanday ishlaydi

`EMAIL_BACKEND` standart holatda Django'ning **konsol backend**iga
o'rnatilgan — tasdiqlash kodi `runserver` ishlayotgan terminalga (yoki
`docker compose logs -f backend`ga) to'g'ridan-to'g'ri chiqadi:

```
Tasdiqlash kodingiz: 048213
Kod 15 daqiqadan so'ng amal qilishdan to'xtaydi.
```

**Jarayon:**
1. Xodim ro'yxatdan o'tadi → hisob faol emas, email tasdiqlanmagan.
2. Xodim 6 xonali kodni kiritadi → hisob faol/tasdiqlangan bo'ladi.
3. **Profil darhol ochiq bo'ladi.** Admin bosqichi yo'q. Xodim darhol
   tizimga kirishi mumkin va uning profili darhol qidiruvda ko'rinadi.

## Demo ma'lumotlar

`python manage.py seed_data` ishga tushirilgandan so'ng (faqat bo'limlar —
demo xodimlar yaratilmaydi; to'liq jarayonni sinash uchun sayt orqali
haqiqiy hisoblar ro'yxatdan o'tkazing).

Admin hisobi: `python manage.py createsuperuser` orqali o'zingiz
o'rnatgan qiymatlar.

## Backend testlarini ishga tushirish

```bash
cd backend
python manage.py test
```

Quyidagilarni qamrab oladi: ro'yxatdan o'tish + tasdiqlash (faol
emas → faol/tasdiqlangan), kirish (foydalanuvchi nomi, email, noto'g'ri
parol, tasdiqlanmagan hisob bloklangani), ochiq qidiruv (autentifikatsiya
talab qilinmaydi, ism/bo'lim filtrlari, tasdiqlanmagan hisoblar hech
qachon ko'rinmaydi, tasdiqlangan hisoblar eski `is_public`/
`moderation_status` ustunlari qiymatidan qat'i nazar ko'rinadi,
kartochkalarda `works_count` bor), ochiq profil sahifasi (email/
foydalanuvchi nomini hech qachon ochmaydi; `works_count` va
`works_by_category`ni o'z ichiga oladi), va ilmiy ishlar (har bir
kategoriya bo'yicha majburiy-maydon tekshiruvi, faqat-PDF + magic-byte
tekshiruvi, sonlar chegarasi yo'q, yangilashda faqat fayl almashtirish,
xodimlar o'rtasida egalik izolyatsiyasi, DOI takrorlanish ogohlantirishi +
tasdiqlash orqali bekor qilish, turli xodimlar o'rtasida DOI'ni qayta
ishlatishga ruxsat berilishi, ochiq ishlar endpointi faqat tasdiqlangan
xodimlar bilan cheklangani va kategoriya bo'yicha filtrlash) — **jami 88
ta test**, jumladan ikkita alohida fayl:

- `specialists/test_reports.py` — har bir kategoriya/klassifikatsiya
  kombinatsiyasi uchun `report_code`ning to'g'ri hisoblanishi, bo'lim
  jami ko'rsatkichlari hech qachon "jumladan" (subset) qatorlarni ikki
  marta hisoblamasligi, 2.1-band kvartil matritsasi, DOI asosidagi
  institut birlashtirishi (bir xil DOI turli xodimlarda institut
  bo'yicha bir marta hisoblanadi, lekin har bir shaxsiy hisobotda
  ko'rinadi), kategoriya bo'yicha yil-manbasini tanlash, anjumanda
  ishtirok uchun PDF istisnosi, va hisobot endpointlariga kirish
  nazorati (anonim/faqat-xodim bo'lmagan foydalanuvchilar rad etiladi).
- `specialists/test_report_lines.py` — har bir band/kvartil-katak/bo'lim-jami
  bo'yicha batafsil ko'rish soni hisobot umumiy ko'rsatkichiga aniq mos
  kelishi (to'g'ridan-to'g'ri tekshiriladi, shunchaki taxmin qilinmaydi),
  `/reports/me/line/*`da egalik izolyatsiyasi, `/reports/institute/line/*`da
  faqat-xodim tekshiruvi, ZIP tarkibi (noyob nomlar, sertifikatsiz
  yozuvlarni o'tkazib yuborish, manifest borligi), institut oynasida har
  bir hammuallif ish uchun bitta birlashtirilgan qator, va oqim (streaming)
  yo'lini tekshirish uchun 50 ta yozuvlik sinov.

---

## API ma'lumotnomasi

Barcha endpointlar `/api/` prefiksi bilan boshlanadi.

| Metod | Yo'l | Autentifikatsiya | Izoh |
|---|---|---|---|
| GET | `/departments/` | Ochiq | tanlov ro'yxati manbai |
| GET | `/specialists/?name=&department=&page=` | Ochiq (60/daq) | har bir tasdiqlangan, faol xodim; kartochkalarda `works_count` bor |
| GET | `/specialists/{id}/` | Ochiq (60/daq) | `works_count` + `works_by_category`ni o'z ichiga oladi |
| GET | `/specialists/{id}/works/?category=&page=&ordering=` | Ochiq (60/daq) | ma'lum bir tasdiqlangan xodimning ishlari |
| POST | `/auth/register/` | Ochiq | multipart, bitta so'rov (rasm bilan birga; ishlar faqat shaxsiy kabinetdan) |
| POST | `/auth/verify-email/` | Ochiq | `{email, code}` |
| POST | `/auth/resend-code/` | Ochiq | 60 soniya kutish, soatiga 5 marta |
| POST | `/auth/login/` | Ochiq | `{login, password}` → JWT |
| POST | `/auth/refresh/` | Ochiq | `{refresh}` → yangi access token |
| GET | `/me/` | JWT | asosiy hisob ma'lumoti, `is_staff` bilan birga |
| GET/PATCH | `/specialists/me/` | JWT, tasdiqlangan | o'z profili, rasmni almashtirish/o'chirish |
| GET/POST | `/specialists/me/works/?category=&page=&ordering=&report_code=` | JWT, tasdiqlangan | o'z ishlarini ro'yxatlash/yaratish, sonlar chegarasi yo'q |
| GET/PATCH/DELETE | `/specialists/me/works/{id}/` | JWT, tasdiqlangan | bitta ishni tahrirlash (PDF almashtirish bilan) yoki o'chirish |
| GET | `/reports/me/?year=&date_from=&date_to=` | JWT, tasdiqlangan | tuzilgan hisobot: bo'limlar, kvartil matritsasi, klassifikatsiyalanmagan ro'yxat |
| GET | `/reports/me/line/?code=&year=` | JWT, tasdiqlangan | bitta band/kvartil-katak/bo'lim-jami ortidagi yozuvlar (faqat o'ziniki) |
| GET | `/reports/me/line/zip/?code=&year=` | JWT, tasdiqlangan (10/daq) | shu bandning o'z PDF fayllari oqim (stream) ko'rinishidagi ZIP |
| GET | `/reports/me/export/?year=` | JWT, tasdiqlangan | shaxsiy hisobotning Excel'ga yuklab olinishi |
| GET | `/reports/institute/?year=&department=&employee=` | JWT, **faqat staff** | birlashtirilgan institut jami ko'rsatkichlari + laboratoriya/xodim bo'yicha taqsimot |
| GET | `/reports/institute/line/?code=&year=&department=&employee=` | JWT, **faqat staff** | bitta band ortidagi birlashtirilgan yozuvlar, hammuallif ro'yxati bilan |
| GET | `/reports/institute/line/zip/?code=&year=&department=` | JWT, **faqat staff** (10/daq) | oqim ko'rinishidagi ZIP, har bir birlashtirilgan ish uchun bitta fayl (asosiy muallif nusxasi ustunlik qiladi) |
| GET | `/reports/institute/export/?year=&department=` | JWT, **faqat staff** | institut hisobotining Excel'ga yuklab olinishi |

**`ScientificWork` kategoriyalari** (`category` maydoni): `foreign_article`,
`local_article`, `thesis`, `conference_participation`, `patent`,
`other_publication`. Majburiy maydonlar har bir kategoriya bo'yicha farq
qiladi — qarang:
`specialists/serializers.py::ScientificWorkSerializer.CATEGORY_REQUIRED_FIELDS`
(shuningdek `validate()` ichidagi maqola kvartillari va tezis mahalliy-
anjuman darajasi bo'yicha shartli qoidalar). PDF fayli **`conference_participation`dan
tashqari** har bir kategoriyada yaratishda majburiy; `PATCH` uni
almashtirishi mumkin, lekin hech qachon o'chira olmaydi. Bir xil
xodimning DOI takrorlanishi so'rovda `confirm_duplicate=true`
ko'rsatilmagan bo'lsa, `{"code": "duplicate_doi", ...}` (400) qaytaradi.

Har bir yozuv hisoblab chiqilgan, indekslangan `report_code`ni
(`specialists/report_codes.py::compute_report_code`) o'z ichiga oladi —
bu uni aynan bitta rasmiy yillik hisobot bandiga (`2.1`–`6.7`) bog'laydi;
har bir saqlashda qayta hisoblanadi va `python manage.py recalc_report_codes`
orqali orqaga qaytarib to'ldirilishi mumkin.

**Band bo'yicha batafsil ko'rish `code` qiymatlari** (`/reports/*/line*`
endpointlari uchun): oddiy band kodi (`2.1`), birlashtirilgan mahalliy-
anjuman kodi (`3.4`), subset kodi (`5.2`/`5.4`), kvartil bilan bog'liq
maqola kodi (`2.1:scopus:Q1`), yoki bo'limning "Jami"si uchun bo'lim ID'si
(`II`..`VI`). Hisobotda ko'rsatilgan son va oynadagi qatorlar ro'yxati
xuddi bir xil `resolve_line_records()` funksiyasi orqali ishlab
chiqariladi, shuning uchun ular hech qachon bir-biridan farqlanmaydi —
bu to'g'ridan-to'g'ri `specialists/test_report_lines.py`da tekshiriladi.

ZIP fayllar `zipstream-ng` yordamida haqiqiy generator asosidagi oqim
sifatida (`StreamingHttpResponse`) quriladi — fayllar ochiladi, 64KB
qismlarda o'qiladi va birma-bir yopiladi; hech narsa to'liq xotirada
saqlanmaydi yoki vaqtinchalik faylga yozilmaydi. Har bir ZIP nimalar
kiritilgani va sertifikati yo'qligi sababli o'tkazib yuborilgan
yozuvlarni ko'rsatuvchi `_haqida.txt` manifest faylini o'z ichiga oladi.

## Kelajakdagi ishlar (seysmologiya texnik topshirig'ining 10-bandi va o'zgartirish so'rovi hujjatlari bo'yicha)

- Profilda ORCID / Google Scholar / Scopus havolalari + umumiy nashrlar ro'yxati.
- Bo'limlarni va ularning xodimlarini ko'rsatuvchi "Bo'limlar" ko'rish sahifasi.
- Til almashtirgich (o'zbek / rus / ingliz) — `i18n/uz.js` tuzilishi bunga tayyor.
- Xorijiy/mahalliy maqola formasida Crossref API orqali "DOI orqali to'ldirish" avtomatik to'ldirish.
- Xodimlarni klassifikatsiyalanmagan yozuvlar bo'ylab birma-bir olib o'tuvchi "Ma'lumotlarni to'ldirish" yordamchisi.
- Agregatsiya sekinlashib qolsa, (yil, bo'lim) bo'yicha institut hisoboti natijalarini keshlash.
- Hisobot suratlari (topshirilgan yilni "muzlatib" qo'yish, shunda keyingi tahrirlar uni o'zgartirmaydi).
- Imzolash uchun hisobot shaklining PDF eksporti.

---

## Qo'lda sinash ro'yxati

1. `http://localhost:5173` sahifasini oching — seysmogramma motivi bilan
   markazlashtirilgan hero, qidiruv konsoli (ism + bo'lim), yuqori chapda
   logotip, yuqori o'ngda Kirish/Ro'yxatdan o'tish.
2. Ism bo'yicha va alohida bo'lim bo'yicha qidiring — natijalar tizimga
   kirmasdan to'g'ri filtrlanadi; har bir kartochkada jami ishlar soni
   ko'rsatiladi.
3. Yangi xodimni ro'yxatdan o'tkazing, email kodini tasdiqlang, tizimga
   kiring → `/dashboard`.
4. **"Ilmiy ishlarim"** bo'limida barcha oltita kategoriyani qamrab
   oluvchi yozuvlar qo'shing (jumladan kamida bitta Scopus/WoS maqolasi
   `indexed_in = both` bilan va turli Scopus/WoS kvartillari bilan,
   ikkala mahalliy-anjuman darajasida bittadan tezis, sertifikatsiz
   bitta Anjumanda ishtirok, va xorijda chiqqan bitta monografiya).
5. PDF'siz yozuv saqlashga urinib ko'ring (Anjumanda ishtirokdan boshqa
   har qanday kategoriya) — xatoni tasdiqlang; Anjumanda ishtirok
   fayilsiz ham muvaffaqiyatli saqlanishini, jadvalda "Sertifikat
   yuklanmagan" ko'rsatilishini tasdiqlang.
6. **"Hisobot"**ni oching — har bir bo'limning bandlari va jami
   ko'rsatkichlarini tekshiring (5.2 bo'lim V jamisini oshirib
   yubormasligi kerak). Har bir noldan farqli son, jumladan 2.1
   kvartil kataklari va har bir bo'limning "Jami"si, tagiga chizilgan,
   bosiladigan tugma bo'lishi kerak; nol sonlar oddiy matn bo'lib qoladi.
7. Bir sonni bosing → batafsil ko'rish oynasi aynan shuncha yozuvni
   ro'yxatlashini, muallif ustuni yo'qligini, shu kategoriya uchun to'g'ri
   metama'lumotni, va ishlaydigan har-bir-yozuv yuklab olish havolasini
   (yoki fayl bo'lmasa "Sertifikat yo'q" degan yozuvni) tasdiqlang.
   **"Barchasini ZIP qilib yuklash"**ni bosing va ZIP to'g'ri fayllar
   hamda `_haqida.txt` manifesti bilan ochilishini tasdiqlang.
8. Dashboard'dan Excelga yuklang — fayl yuklab olinishini va bo'lim
   sarlavhalari, raqamlangan bandlar, kvartil ustunlari bilan
   ochilishini tasdiqlang.
9. Shu xodimning ochiq profilini oching — oltita bo'lim (faqat bo'sh
   bo'lmaganlari) va har bir qatorning PDF yuklab olinishini tasdiqlang.
10. Ikkinchi xodim sifatida, birinchi xodimning ishi bilan **bir xil
    DOI**ga ega ish ro'yxatdan o'tkazing (hammuallif sifatida). `is_staff`
    hisobi sifatida **"Institut hisoboti"**ni oching — baham ko'rilgan
    ish institut jamisida bir marta hisoblanishini ("N ta takroriy yozuv
    birlashtirildi" eslatmasini) tasdiqlang, shu bandning sonini bosing,
    va oyna **ikkala muallif ko'rsatilgan bitta qator** (asosiy muallif
    belgilangan) ko'rsatishini, ZIP faylida aynan bitta, asosiy
    muallifning familiyasi bilan nomlangan fayl borligini tasdiqlang.
11. Faqat-xodim (staff bo'lmagan), tizimga kirgan hisob `/admin-report`dan
    chetlatilishini, `/api/reports/institute/*`dan 403 xatosi olishini,
    va `/api/reports/me/line/*` orqali boshqa xodimning yozuvlarini
    ololmasligini (faqat o'zinikini ko'rishini) tasdiqlang.
12. `/foo/bar` kabi mavjud bo'lmagan URL'ga kiring → 404 sahifasi.
