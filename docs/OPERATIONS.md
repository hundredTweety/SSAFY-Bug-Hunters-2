# 배포 · 운영 가이드

[← README로 돌아가기](../README.md)

## 1. 환경변수

`.env.example`을 참고해요. 운영 환경(`DEBUG=False`)에서 아래 값이 없으면 서버가 시작되지 않아요.

| 변수 | 설명 |
|---|---|
| `DJANGO_SECRET_KEY` | 40자 이상 무작위 값 (Render가 자동 생성) |
| `DATABASE_URL` | Neon pooled PostgreSQL URL (`sslmode=require`) |
| `RAID_INVITE_CODE` | 반 참여 코드. 서버에서만 확인하고 HTML에는 넣지 않아요 |
| `RAID_MAX_HP` / `RAID_DAMAGE` / `RAID_MAX_CLEARS_PER_PLAYER` | 보스 HP(1000) / 1회 데미지(20) / 1인 공격 상한(3) |
| `RAID_RESULTS_PUBLIC` | `1`이면 격파 전에도 리포트를 공개해요 |
| `ADMIN_BOOTSTRAP_PASSWORD` | 16자 이상. 첫 배포 때 관리자 계정을 만든 뒤 **바로 삭제**해요 |

> Neon 접속 문자열, 시크릿 키, 참여 코드는 절대 커밋하지 않아요.

## 2. Render + Neon 배포

1. Neon에서 무료 프로젝트를 만들고 **pooled connection string**을 복사해요.
2. Render에서 이 저장소를 Blueprint(`render.yaml`)로 연결해요. `render.yaml`은 30일 후 만료되는 Render 무료 PostgreSQL을 만들지 않아요.
3. `DATABASE_URL`, `RAID_INVITE_CODE`, (처음 한 번) `ADMIN_BOOTSTRAP_PASSWORD`를 입력해요.
4. 배포 과정
   - `build.sh`: 패키지 설치 → `collectstatic` → `check --deploy`
   - `start.sh`: `migrate` → `seed_questions` → `bootstrap_admin` → Gunicorn 실행
5. 배포 후 확인
   - `/healthz/`가 `ok`를 반환하는지 확인해요(DB 연결까지 확인해요).
   - 서로 다른 브라우저 두 개로 접속해서 보스 HP가 공유되는지 확인해요.
   - 관리자 계정이 만들어졌으면 `ADMIN_BOOTSTRAP_PASSWORD`를 지워요.

## 3. 문제 관리

- 문제 원본은 `raid/question_bank.json`이에요. 수정한 뒤에는 `python scripts/validate_bank.py`로 검증해요.
- `seed_questions`는 **없는 문제만 추가**하고, 관리자 화면에서 고친 내용은 덮어쓰지 않아요.
- 행사 중에 문제를 고칠 때는 `/admin/`을 써요.

## 4. 운영 명령어

```bash
python manage.py seed_questions         # 문제 시딩 (멱등)
python manage.py bootstrap_admin        # 환경변수로 초기 관리자 1회 생성
python manage.py reset_raid --confirm   # 제출 · 해결 기록 삭제, 보스 HP 초기화 (참여자 · 문제는 유지)
```

## 5. 개인정보 · 데이터

- 닉네임, 문제별 답안, 정답 여부, 제출 시각, 힌트 사용 여부만 저장해요. 이메일이나 전화번호는 받지 않아요.
- 닉네임은 본인 인증 수단이 아니라서 상품 지급 기준으로 쓰지 않아요.
- 사용자 화면에는 다른 사람의 개별 기록을 보여주지 않아요.
- 운영자 CSV에는 닉네임과 응답 기록이 들어 있으니 외부에 공유하지 않아요(`.gitignore`로 커밋도 막아 두었어요).
- 행사가 끝나면 보관 기간을 정한 뒤 관리자 화면에서 `Player`와 연관 기록을 삭제해요.

## 6. 게임 규칙 요약

- 미션 32개: EASY 6 / NORMAL 9 / HARD 9, 4개 분야 각 8개
- 버그 줄 선택 → (서버 검증) → 4지선다 수정안 선택
- 최초 해결 시 20 데미지, 같은 미션은 중복 데미지 없음, 1인 최대 3회 공격
- 보스 HP 1,000 = 유효 공격 50회. 1인 3회 상한이라 **최소 17명**이 참여해야 격파돼요
- 개인 순위는 없고, 반 혜택은 참여 여부와 관계없이 모두에게 똑같이 줘요
