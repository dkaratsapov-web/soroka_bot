# Автодеплой на Yandex Cloud (VM + GitHub Actions)

Схема: пуш в GitHub → GitHub Actions собирает Docker-образ → пушит в **Yandex Container
Registry** → по SSH перезапускает контейнер на **виртуалке (Compute Cloud)**.
Бот остаётся на Python + long-polling, код не переписываем.

Workflow уже лежит в репозитории: `.github/workflows/deploy.yml`.
Ниже — **разовая** настройка (делается один раз). После неё каждая правка деплоится сама.

---

## Что понадобится
- Аккаунт в Yandex Cloud (есть стартовый грант для новых аккаунтов).
- Установленный локально `yc` CLI (https://cloud.yandex.ru/docs/cli/quickstart) — для разовой настройки.
  Можно сделать и через веб-консоль, но командами быстрее.

Везде ниже подставьте свои значения вместо `<...>`.

---

## Шаг 1. Container Registry (куда складывать образы)
```bash
yc container registry create --name soroka-registry
yc container registry list   # запомните ID реестра — это YC_REGISTRY_ID
```

## Шаг 2. Сервисный аккаунт для GitHub Actions (пуш образов)
```bash
yc iam service-account create --name github-pusher

# дать право пушить в реестр
yc container registry add-access-binding soroka-registry \
  --role container-registry.images.pusher \
  --service-account-name github-pusher

# создать authorized-ключ (JSON) — его положим в секрет GitHub
yc iam key create --service-account-name github-pusher --output github-pusher-key.json
```
Файл `github-pusher-key.json` понадобится для секрета `YC_SA_KEY` (шаг 6). **Не коммитьте его.**

## Шаг 3. Сервисный аккаунт для VM (пул образов)
```bash
yc iam service-account create --name vm-puller
yc container registry add-access-binding soroka-registry \
  --role container-registry.images.puller \
  --service-account-name vm-puller
```

## Шаг 4. Виртуалка (Compute Cloud)
Создайте VM (Ubuntu 22.04, минимальной конфигурации хватит — 2 vCPU / 1–2 ГБ).
Привяжите к ней сервисный аккаунт `vm-puller` и добавьте свой SSH-публичный ключ.
Через консоль это пара кликов; либо командой `yc compute instance create ...`.

После создания зайдите на VM по SSH и подготовьте окружение:
```bash
# Docker
curl -fsSL https://get.docker.com | sudo sh

# yc CLI + авторизация Docker в реестре через сервисный аккаунт VM (без ключей)
curl -sSL https://storage.yandexcloud.net/yandexcloud-yc/install.sh | bash
exec -l $SHELL
yc container registry configure-docker

# файл с секретами для бота (его читает контейнер)
sudo mkdir -p /opt/soroka_bot
sudo tee /opt/soroka_bot/.env >/dev/null <<'EOF'
BOT_TOKEN=<ВАШ_ТОКЕН_ОТ_BOTFATHER>
WELCOME_IMAGE=welcome.jpg
EOF
```
> `WELCOME_IMAGE=welcome.jpg` указывает на файл **внутри образа** (он копируется при сборке).
> Токен живёт только на VM, в репозиторий не попадает.

## Шаг 5. SSH-ключ для GitHub Actions
GitHub Actions должен заходить на VM. Сгенерируйте отдельную пару ключей:
```bash
ssh-keygen -t ed25519 -f gh-deploy-key -N ""
```
- Публичный `gh-deploy-key.pub` — добавьте в `~/.ssh/authorized_keys` пользователя на VM.
- Приватный `gh-deploy-key` — положите в секрет `VM_SSH_KEY` (шаг 6).

## Шаг 6. Секреты в GitHub
Repo → **Settings → Secrets and variables → Actions → New repository secret**:

| Секрет | Значение |
|---|---|
| `YC_REGISTRY_ID` | ID реестра из шага 1 |
| `YC_SA_KEY` | **всё содержимое** файла `github-pusher-key.json` (шаг 2) |
| `VM_SSH_HOST` | публичный IP виртуалки |
| `VM_SSH_USER` | пользователь на VM (например `yc-user` или `ubuntu`) |
| `VM_SSH_KEY` | приватный ключ `gh-deploy-key` (шаг 5) |

---

## Готово
После настройки:
1. Пуш в ветку `main` (или текущую рабочую) запускает `.github/workflows/deploy.yml`.
2. Через ~1–2 минуты обновлённый бот уже работает на VM.
3. Контейнер перезапускается автоматически (`--restart unless-stopped`), переживает перезагрузку VM.

Проверить статус на VM: `docker ps` и `docker logs -f soroka-bot`.

---

## Важные напоминания
- Сделайте бота **администратором** канала `@sorokavmarketinge` — иначе проверка подписки не работает.
- Прод-ветка по умолчанию в workflow — `main`. Если деплоите из рабочей ветки —
  она уже добавлена в триггер; для прода лучше влить изменения в `main` (через Pull Request).
- Файлы ключей (`*-key.json`, `gh-deploy-key`) держите вне репозитория.
