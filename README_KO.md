# AI Work Scheduler

<p align="center">
  <img src="docs/assets/app-icon.png" alt="AI Work Scheduler 아이콘" width="160">
</p>

메시지에서 **Task / Event / Follow-up 후보**를 추출하되, AI가 사용자 승인 없이 일정이나 업무를 자동 확정하지 못하도록 분리한 범용 Workflow Core입니다.

[English README](README.md)

## 핵심 구조

```text
Message
  -> 전처리
  -> AI / Rule 기반 추출
  -> Candidate Action 1:N
  -> SQLite + 중복 방지
  -> 사용자 검토
  -> 승인된 Action
  -> 선택적 실행 Adapter
```

핵심 원칙은 다음과 같습니다.

- Message와 Action을 별도 객체로 관리
- 하나의 Message에서 여러 Action 허용
- AI 결과는 항상 **후보** 상태로 저장
- 원문에 날짜가 없으면 `null` 유지 — 임의 기한 생성 금지
- 원문의 날짜/시간 표현을 그대로 보존
- 동일 Message/Action 재처리 시 중복 생성 방지
- 실행 전 명시적 승인 필요
- Outlook/Gmail/Calendar 같은 외부 시스템은 Adapter로 분리

공개판에는 회사·고객·사내 Endpoint·Credential·실제 메일 내용이 포함되어 있지 않습니다.

## Windows 설치파일

[Cloud PC Outlook Scheduler v2.2.2 설치](releases/CloudPCScheduler_Setup_v2.2.2.exe)

- Windows와 데스크톱 Outlook이 필요합니다.
- AI Endpoint, Model, API Key는 설치 후 사용자가 직접 설정합니다.
- 회사명, 사내 URL, 사내 이메일 및 회의실 예약·입실·취소 기능을 포함하지 않습니다.
- SHA-256: `A615F0DBC15E8ECBFF34D4A6CBA45D25B568453A9B220C5E36718EE19485DDF3`

## 빠른 실행

Python 3.10+이며 런타임은 표준 라이브러리만 사용합니다.

```bash
python -m ai_work_scheduler --db demo.db prompt examples/message.json
```

합성 AI 응답 예제를 저장:

```bash
python -m ai_work_scheduler --db demo.db ingest \
  examples/message.json examples/model_output.json

python -m ai_work_scheduler --db demo.db list
```

후보 승인:

```bash
python -m ai_work_scheduler --db demo.db approve 1
```

승인되지 않은 Action은 `executed` 상태로 바꿀 수 없습니다.

## Action 의미

- `task`: 사용자가 지금 직접 수행해야 할 일
- `event`: 시간/일정이 있는 이벤트
- `follow_up`: 다른 사람/시스템의 회신·승인·완료를 기다린 뒤 다시 확인할 일
- `ignore`: Action 없음

## v0.1 포함 범위

- 범용 Message 모델
- Task / Event / Follow-up / Ignore
- Message : Action = 1:N
- AI Extraction Prompt / JSON Contract
- 날짜 원문 보존 규칙
- 보수적인 회신 이력 분리
- SQLite 상태 저장
- Idempotency
- Candidate -> Approved/Rejected/Held -> Executed 상태 제어
- CLI / 합성 예제 / 테스트

## 아직 포함하지 않음

- Outlook / Gmail Collector
- Calendar / Task Adapter
- Reply Draft Adapter
- 직접 LLM API 호출 Adapter
- GUI Approval Inbox
- 자동 날짜 정규화
- Background Polling

위 항목은 향후 확장 지점이며 현재 구현됐다는 의미가 아닙니다.

## 설계 원칙

**AI는 제안하고, 시스템은 기억하며, 사람은 승인하고, Adapter가 실행한다.**
