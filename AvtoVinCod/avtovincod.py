# -*- coding: utf-8 -*-
"""
Проверка автомобиля через API AvtoVinCod (api.avtovincod.ru).

Запуск: двойной щелчок по «Запуск.bat» (или по этому файлу).
Откроется страница в браузере. Окно программы не закрывайте, пока работаете.
Токен хранится в файле avtovincod_token.txt рядом с программой.
Нужен Python 3.8+ (дополнительные пакеты не нужны).
"""
import json
import os
import socket
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE = os.environ.get('AVC_BASE', 'https://api.avtovincod.ru')
HERE = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(HERE, 'avtovincod_token.txt')
PORT = 8738

ALLOWED = {
    'balance', 'score', 'score-body', 'vin', 'body', 'gibdd-archive', 'gos2vin', 'pledge', 'lizing',
    'accidents', 'accidents-rt', 'hidden-damage', 'lawsuits', 'taxi', 'sharing', 'customs', 'customs-fts',
    'elpts', 'decode', 'brief', 'vin2gos', 'plate-history', 'autopark', 'pros-cons', 'recalls', 'price',
    'probeg', 'service', 'osago', 'osago-history', 'offers', 'nomerogram', 'vin-precheck', 'auction-lots',
    'usa-history', 'usa-score', 'usa-photos', 'by-history', 'vag-equipment-doc',
}

PAGE = r'''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Проверка авто — AvtoVinCod</title>
<style>
:root{--bg:#f4f5f7;--card:#fff;--text:#1d2129;--muted:#6b7280;--accent:#1f5eff;--ok:#127a3a;--okbg:#e8f6ee;--warn:#9a4a00;--warnbg:#fff3e0;--err:#b91c1c;--errbg:#fde8e8;--line:#e5e7eb}
*{box-sizing:border-box}
body{margin:0;font:15px/1.45 -apple-system,Segoe UI,Roboto,Arial,sans-serif;background:var(--bg);color:var(--text)}
.wrap{max-width:1080px;margin:0 auto;padding:20px 16px 60px}
h1{font-size:22px;margin:0}
.top{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:14px}
.bal{font-size:14px;color:var(--muted)} .bal b{color:var(--text)}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;margin-bottom:14px}
input[type=text],input[type=password]{font:inherit;padding:11px 13px;border:1px solid #cfd4dc;border-radius:8px;outline:none}
input:focus{border-color:var(--accent);box-shadow:0 0 0 3px #1f5eff22}
#q{flex:1 1 340px;font-family:ui-monospace,Consolas,monospace;font-size:18px;letter-spacing:.5px;text-transform:uppercase}
.row{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
button{font:inherit;padding:11px 18px;border:0;border-radius:8px;background:var(--accent);color:#fff;cursor:pointer;font-weight:600}
button:disabled{opacity:.55;cursor:default}
button.sec{background:#eef2ff;color:var(--accent);font-weight:500}
button.small{padding:6px 11px;font-size:13px}
.hint{font-size:13px;color:var(--muted)}
.kind{font-size:13px;padding:3px 9px;border-radius:20px;background:#eef2ff;color:var(--accent)}
.groups{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:4px 18px;margin-top:10px}
.gtitle{grid-column:1/-1;font-weight:700;margin-top:10px;display:flex;gap:10px;align-items:center}
label.ck{display:flex;gap:8px;align-items:flex-start;padding:3px 0;cursor:pointer}
label.ck .pr{margin-left:auto;color:var(--muted);white-space:nowrap;font-size:13px}
label.ck.na{opacity:.45}
.presets{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
.total{font-weight:700}
.flags{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px}
.flag{padding:6px 10px;border-radius:8px;font-size:14px}
.flag.ok{background:var(--okbg);color:var(--ok)} .flag.warn{background:var(--warnbg);color:var(--warn)} .flag.err{background:var(--errbg);color:var(--err)}
.res{border:1px solid var(--line);border-radius:10px;margin-bottom:10px;background:#fff}
.res>summary{list-style:none;cursor:pointer;padding:11px 14px;display:flex;gap:10px;align-items:center}
.res>summary::-webkit-details-marker{display:none}
.res .st{font-size:12px;padding:2px 8px;border-radius:12px;white-space:nowrap}
.st.run{background:#eef2ff;color:var(--accent)} .st.ok{background:var(--okbg);color:var(--ok)} .st.warn{background:var(--warnbg);color:var(--warn)} .st.err{background:var(--errbg);color:var(--err)} .st.none{background:#f1f2f4;color:var(--muted)}
.res .nm{font-weight:600} .res .sm{color:var(--muted);font-size:13px;margin-left:auto;text-align:right}
.body{padding:0 14px 14px;overflow-x:auto}
table.kv{border-collapse:collapse;width:100%;font-size:14px}
table.kv td{padding:5px 6px;border-bottom:1px solid #f0f1f3;vertical-align:top}
table.kv td.k{color:var(--muted);width:34%}
.item{border-left:3px solid #dfe3ea;padding-left:10px;margin:8px 0}
.thumbs img{height:110px;border-radius:6px;margin:4px 6px 0 0;border:1px solid var(--line)}
a{color:var(--accent)}
.banner{padding:10px 12px;border-radius:8px;background:var(--warnbg);color:var(--warn);margin-bottom:10px;font-size:14px}
.modal{position:fixed;inset:0;background:#0007;display:none;align-items:center;justify-content:center;padding:16px;z-index:9}
.modal.on{display:flex}
.modal .card{max-width:560px;width:100%}
code{font-family:ui-monospace,Consolas,monospace;font-size:13px;background:#f1f2f4;padding:1px 5px;border-radius:4px}
@media print{.noprint{display:none!important}.res{break-inside:avoid}body{background:#fff}}
</style>
</head>
<body>
<div class="wrap">
  <div class="top">
    <h1>Проверка автомобиля</h1>
    <div class="row noprint">
      <span class="bal">Баланс: <b id="bal">—</b></span>
      <button class="sec small" id="refreshBal">Обновить</button>
      <button class="sec small" id="tokenBtn">Токен</button>
    </div>
  </div>

  <div class="card noprint">
    <form id="f" class="row">
      <input type="text" id="q" placeholder="VIN, номер кузова или госномер" autocomplete="off" spellcheck="false">
      <button type="submit" id="go">Проверить</button>
      <button type="button" class="sec" id="test">Тест (бесплатно)</button>
    </form>
    <div class="row" style="margin-top:8px">
      <span class="kind" id="kind">введите данные</span>
      <span class="hint" id="kindHint"></span>
    </div>

    <div class="presets">
      <span class="hint" style="align-self:center">Наборы:</span>
      <button class="sec small" data-preset="base">Базовый</button>
      <button class="sec small" data-preset="ru">Всё по РФ</button>
      <button class="sec small" data-preset="all">Всё</button>
      <button class="sec small" data-preset="none">Снять всё</button>
      <span style="margin-left:auto" class="hint">Выбрано: <span class="total" id="total">0 ₽</span> (базовые цены, списание только за найденные данные)</span>
    </div>
    <div class="groups" id="checks"></div>
  </div>

  <div id="report" style="display:none">
    <div class="card">
      <div class="top" style="margin:0">
        <div>
          <div style="font-size:20px;font-weight:700" id="rTitle"></div>
          <div class="hint" id="rSub"></div>
        </div>
        <div class="row noprint">
          <button class="sec small" id="copy">Скопировать текстом</button>
          <button class="sec small" id="save">Сохранить отчёт</button>
          <button class="sec small" id="print">Печать / PDF</button>
          <button class="sec small" id="expand">Раскрыть все</button>
        </div>
      </div>
      <div id="testBanner"></div>
      <div class="flags" id="flags"></div>
    </div>
    <div id="results"></div>
  </div>
</div>

<div class="modal" id="tokModal">
  <div class="card">
    <h3 style="margin-top:0">API-токен AvtoVinCod</h3>
    <p class="hint">Скопируйте токен в личном кабинете avtovincod.ru (блок «API-токен») и вставьте сюда. Он сохранится в файле <code>avtovincod_token.txt</code> рядом с программой и никуда, кроме api.avtovincod.ru, не отправляется.</p>
    <input type="password" id="tokIn" style="width:100%" placeholder="96 символов" autocomplete="off">
    <div class="row" style="margin-top:12px">
      <button id="tokSave">Сохранить</button>
      <button class="sec" id="tokCancel">Отмена</button>
      <span class="hint" id="tokMsg"></span>
    </div>
  </div>
</div>

<script>
'use strict';
const $ = s => document.querySelector(s);
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const money = n => (Math.round(n*100)/100).toLocaleString('ru-RU') + ' ₽';

// ---------- Список проверок ----------
// p: какие идентификаторы принимает (в порядке предпочтения)
// ep: если для разных идентификаторов разные адреса
const GROUPS = [
  ['ru','Юридическая чистота и история (РФ)'],
  ['tech','Данные автомобиля'],
  ['use','Эксплуатация, страховка, объявления'],
  ['foreign','Иностранные отчёты (дорогие)'],
];
const CHECKS = [
  {id:'score', t:'Владельцы, ограничения, розыск', price:20, p:['vin','body'], ep:{vin:'score',body:'score-body'}, g:'ru', base:1},
  {id:'gibdd', t:'История регистрации ГИБДД', price:12, p:['vin','body'], ep:{vin:'vin',body:'body'}, g:'ru'},
  {id:'gibdd-archive', t:'История регистрации (архив)', price:2.5, p:['vin'], g:'ru'},
  {id:'pledge', t:'Залоги (реестр ФНП)', price:2.4, p:['vin','body'], g:'ru', base:1},
  {id:'lizing', t:'Лизинг', price:2.2, p:['vin'], g:'ru', base:1},
  {id:'accidents', t:'ДТП (архив)', price:0.8, p:['vin'], g:'ru', base:1},
  {id:'accidents-rt', t:'ДТП по базе ГИБДД (в реальном времени)', price:19, p:['vin','body'], g:'ru'},
  {id:'hidden-damage', t:'Скрытые ДТП, расчёты ремонта, страх. выплаты', price:8, p:['vin','body'], g:'ru', base:1},
  {id:'lawsuits', t:'Судебные дела (арбитраж)', price:3, p:['vin','plate'], g:'ru'},
  {id:'taxi', t:'Работа в такси', price:1.8, p:['plate','vin'], g:'ru', base:1},
  {id:'sharing', t:'Каршеринг', price:5.4, p:['plate','vin'], g:'ru'},
  {id:'customs', t:'Таможенное оформление', price:1.9, p:['vin'], g:'ru', base:1},
  {id:'customs-fts', t:'ФТС: дата выпуска и утильсбор', price:7.5, p:['vin','body'], g:'ru'},
  {id:'elpts', t:'Электронный ПТС', price:1, p:['vin'], g:'ru'},

  {id:'decode', t:'Расшифровка VIN', price:1.6, p:['vin'], g:'tech'},
  {id:'brief', t:'Краткие данные ТС', price:1, p:['vin','plate'], g:'tech'},
  {id:'vin2gos', t:'Госномер по VIN', price:6, p:['vin'], g:'tech'},
  {id:'plate-history', t:'История госномеров', price:1.5, p:['vin','body'], g:'tech'},
  {id:'autopark', t:'Номер двигателя', price:0.8, p:['vin','body'], g:'tech'},
  {id:'pros-cons', t:'Плюсы и минусы модели', price:0.8, p:['vin','body'], g:'tech'},
  {id:'recalls', t:'Отзывные кампании', price:0.8, p:['vin'], g:'tech'},
  {id:'price', t:'Рыночная оценка', price:0.5, p:['vin'], g:'tech'},

  {id:'probeg', t:'Техосмотры и пробег', price:3.5, p:['vin','plate','body'], g:'use', base:1},
  {id:'service', t:'Сервисная история', price:26, p:['vin'], g:'use'},
  {id:'osago', t:'Полисы ОСАГО', price:1.5, p:['vin','plate','body'], g:'use'},
  {id:'osago-history', t:'История полисов ОСАГО', price:1.7, p:['vin','plate','body'], g:'use'},
  {id:'offers', t:'Объявления о продаже', price:1.5, p:['vin','plate'], g:'use'},
  {id:'nomerogram', t:'Фото из объявлений', price:1.7, p:['plate'], g:'use'},

  {id:'vin-precheck', t:'Есть ли данные в иностранных базах', price:0.2, p:['vin'], g:'foreign'},
  {id:'auction-lots', t:'Аукционы США и Кореи: цены и фото', price:89, p:['vin'], g:'foreign'},
  {id:'usa-history', t:'CARFAX (США и Канада)', price:389, p:['vin'], g:'foreign'},
  {id:'usa-score', t:'AutoCheck (США и Канада)', price:389, p:['vin'], g:'foreign'},
  {id:'usa-photos', t:'Фото с аукционов США (VinHistory)', price:649, p:['vin'], g:'foreign'},
  {id:'by-history', t:'История в Беларуси', price:389, p:['vin'], g:'foreign'},
  {id:'vag-equipment-doc', t:'Комплектация VAG по ETKA (PDF)', price:389, p:['vin'], g:'foreign'},
];
const TEST = {vin:'X7TEST00000000001', plate:'Т000ТТ00', body:'TEST-0000001'};
const KIND_RU = {vin:'VIN', plate:'Госномер', body:'Номер кузова'};

// ---------- Подписи полей ----------
const L = {
  vin:'VIN', bodyNumber:'Номер кузова', body:'Кузов', chassis:'Шасси', chassisNumber:'Номер шасси', model:'Модель', brand:'Марка', make:'Марка',
  year:'Год', color:'Цвет', category:'Категория', engineVolume:'Объём двигателя, см³', powerHp:'Мощность, л.с.', powerKwt:'Мощность, кВт',
  maxWeight:'Разрешённая макс. масса', weightWithoutLoading:'Масса без нагрузки', recordStatus:'Статус записи', lastRegAction:'Последнее рег. действие',
  ownershipPeriods:'Периоды владения', personType:'Владелец', from:'С', to:'По', regNumber:'Госномер', licensePlate:'Госномер', sts:'СТС', pts:'ПТС', num:'Номер', date:'Дата',
  restrictions:'Ограничения', restriction_name:'Ограничение', region:'Регион', organization_name:'Кто наложил', reasons:'Основание', enforcement_number:'Исп. производство',
  enforcement_date:'Дата ИП', osp_address:'Адрес ОСП', searches:'Розыск', status:'Статус', restricted:'Есть ограничения', wanted:'В розыске', spec_wanted:'Спецрозыск (спецпродукция)',
  found:'Найдено', records:'Записи', message:'Сообщение', checkedAt:'Дата проверки', dataNote:'Примечание', archival:'Архивные данные',
  hasAccidents:'Были ДТП', number:'Номер', type:'Тип', place:'Место', damageState:'Состояние', damagePoints:'Точки повреждений', damageDescription:'Описание повреждений',
  vehiclesInvolved:'Участников', department:'Подразделение', damage:'Повреждения', source:'Источник', injured:'Пострадавших', deaths:'Погибших', ownRole:'Роль', participants:'Участники', role:'Роль', reference:'Справка',
  active_count:'Активных залогов', register_date:'Дата регистрации', start_date:'Начало', end_date:'Окончание', pledgors:'Залогодатели', pledgees:'Залогодержатели', objects:'Предмет залога', history:'История', name:'Название',
  eaisto_number:'Номер ЕАИСТО', date_of_diagnosis:'Дата техосмотра', date_of_validity:'Действует до', car_number:'Госномер', car_vin:'VIN', car_body:'Кузов', car_chassis:'Шасси', operator_number:'Оператор ТО', is_valid:'Действующая', car_mileage:'Пробег, км',
  isLeasing:'Был в лизинге', active:'Активных', lessee:'Лизингополучатель', dateStart:'Начало', dateEnd:'Окончание', contract:'Договор', subject:'Предмет', isSublease:'Сублизинг', lessors:'Лизингодатели', lessees:'Лизингополучатели', inn:'ИНН', ogrn:'ОГРН', isActive:'Действует', plannedEnd:'Плановое окончание', stopDate:'Дата прекращения', stopReason:'Причина прекращения', messages:'Сообщения',
  isTaxi:'Такси', regionName:'Регион', permitNumber:'Номер разрешения', carLabel:'Авто', dateFrom:'С', dateTo:'По', dateFgisAdded:'Добавлено во ФГИС', isLiftingDevice:'Подъёмник', isActual:'Действует', carriers:'Перевозчики',
  isCarsharing:'Каршеринг', company:'Компания', checkedBy:'Способ проверки',
  requestDate:'Дата запроса', country:'Страна', releaseDate:'Дата выпуска', releaseTime:'Время выпуска', recyclingFee:'Утильсбор', paymentStatus:'Оплата', customsCode:'Код таможни', personalUse:'Для личного пользования',
  displosal_fee:'Утильсбор', restrictions_status:'Ограничения', customs_restrictions_status:'Таможенные ограничения', last_reg_action:'Последнее рег. действие', production:'Год выпуска',
  policies:'Полисы', companyName:'Страховая', policySerial:'Серия', policyNumber:'Номер', markmodel:'Авто', startDate:'Начало', endDate:'Окончание',
  price:'Цена', mileage:'Пробег', city:'Город', url:'Ссылка', photos:'Фото', match:'Совпадение', excluded:'Исключено',
  description:'Описание', manufacturer:'Производитель', reason:'Причина',
  average:'Средняя', min:'Мин.', max:'Макс.', count:'Количество', similar:'Похожие', dynamics:'Динамика', ads:'Объявления', brandModel:'Модель', oldPrice:'Старая цена', image:'Фото', list:'Список',
  plates:'Госномера', engineNumber:'Номер двигателя',
  reliability:'Надёжность', reliabilityLevel:'Уровень надёжности', bodyCorrosion:'Коррозия кузова', liquidity:'Ликвидность', liquidityLevel:'Уровень ликвидности', pros:'Плюсы', prosList:'Плюсы', cons:'Минусы', consList:'Минусы', vehicle:'Автомобиль', generation:'Поколение', yearFrom:'Год с', yearTo:'Год по', bodyType:'Тип кузова', transmission:'КПП', drive:'Привод',
  summary:'Сводка', accidents:'ДТП', accidents_abroad:'ДТП за рубежом', insurance_payments:'Страховые выплаты', repair_estimates:'Расчёты ремонта', salvage_auctions:'Аукционы битых авто', events:'События', costs:'Стоимость', paint:'Краска', labor:'Работы', parts:'Запчасти', total:'Итого', works:'Работы', items:'Позиции', kind:'Вид', plate:'Госномер', mileage_km:'Пробег, км', car:'Авто',
  mark_model:'Марка и модель', horsepower:'Мощность', engine_type:'Двигатель', engine_vol:'Объём', wheel_type:'Руль', weight:'Масса', response:'Данные',
  variants:'Варианты', title:'Название', modification:'Модификация', market:'Рынок', years:'Годы', start:'Начало', finish:'Конец', current:'Выпускается', doors:'Дверей', code:'Код', text:'Описание', speeds:'Ступеней',
  engine:'Двигатель', series:'Серия', fuelText:'Топливо', fuelCode:'Код топлива', volumeL:'Объём, л', volumeCcm:'Объём, см³', powerPs:'Мощность, л.с.', powerKw:'Мощность, кВт', torqueNm:'Момент, Нм', emission:'Экокласс', layout:'Компоновка', valves:'Клапанов', aspiration:'Наддув', compression:'Степень сжатия', fuelRate:'Расход',
  assembly:'Сборка', plant:'Завод', checkDigit:'Контрольная цифра', registrationMatch:'Совпадает с регистрацией', confirmed:'Подтверждено', decoded:'Расшифрован', full:'Полная расшифровка', bodyName:'Кузов (код)', registerDate:'Дата регистрации', regionCode:'Код региона',
  enginePower:'Мощность, л.с.', vehicleCode:'Категория', totalPhotos:'Фото всего',
  CaseNumber:'Номер дела', RegistrationDate:'Дата', Court:'Суд', Type:'Документ', CaseUrl:'Карточка дела', FileUrl:'Файл', InstanceNumber:'Номер инстанции', ContentTypes:'Содержание',
  record:'Данные ТС', report:'Отчёт', files:'Файлы', web_url:'Открыть отчёт', files_until:'Файлы доступны до', created_at:'Создан', size:'Размер', data:'Данные', facts:'Факты', label:'Параметр', value:'Значение', lots:'Лоты',
  vehicle_title:'Авто', apis:'Отчёты', available:'Доступно', info:'Инфо', connected:'Подключено', key:'Ключ',
  owners:'Владельцев', usage:'Использование', last_state:'Последний штат', branded_title:'Особый статус (title)', total_loss:'Тотальная гибель', service_records:'Сервисных записей', open_recalls_min:'Открытых отзывов', odometer_last:'Последний пробег', km:'км', mi:'миль',
  score:'Оценка', age_years:'Возраст, лет', in_service:'В эксплуатации с', assembly_country:'Страна сборки', fuel:'Топливо', odometer:'Одометр', odometer_unit:'Ед.',
  licensePlate_mask:'', vin_mask:'', bodyNumber_mask:'', chassisNumber_mask:'', regNumber_mask:''
};
const SKIP = new Set(['billing','testMode','query','success','schema','lang','taskId','pollAfterSec','etaSec','maxWaitSec','pledgor_hidden','pledgee_hidden','CaseId','FileName','InstanceLevel','done','pages','page']);
const lab = k => (L[k] !== undefined ? L[k] : k);

function fmtVal(k, v){
  if (v === true) return 'да';
  if (v === false) return 'нет';
  if (typeof v === 'number' && /price|average|min|max|oldPrice/.test(k)) return v.toLocaleString('ru-RU') + ' ₽';
  if (typeof v === 'number' && /mileage/i.test(k)) return v.toLocaleString('ru-RU') + ' км';
  if (k === 'size' && typeof v === 'number') return Math.round(v/1024) + ' КБ';
  const s = String(v);
  if (/^https?:\/\//.test(s)) {
    if (/\.(jpe?g|png|webp|gif)(\?|$)/i.test(s)) return `<a href="${esc(s)}" target="_blank" rel="noopener"><img src="${esc(s)}" style="height:90px;border-radius:6px" loading="lazy"></a>`;
    return `<a href="${esc(s)}" target="_blank" rel="noopener">открыть</a>`;
  }
  if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s.split('-').reverse().join('.');
  if (/^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}/.test(s)) { const [d,t] = s.split(/[T ]/); return d.split('-').reverse().join('.') + ' ' + t.slice(0,5); }
  return esc(s);
}
function isEmpty(v){ return v === null || v === undefined || v === '' || (Array.isArray(v) && !v.length) || (typeof v === 'object' && !Array.isArray(v) && !Object.keys(v).length); }

function renderObj(o, depth){
  depth = depth || 0;
  if (o === null || typeof o !== 'object') return fmtVal('', o);
  if (Array.isArray(o)) {
    if (o.every(x => x === null || typeof x !== 'object')) {
      if (o.every(x => /^https?:\/\/.*\.(jpe?g|png|webp|gif)(\?|$)/i.test(String(x)))) return '<div class="thumbs">' + o.map(x => fmtVal('', x)).join('') + '</div>';
      return o.map(x => fmtVal('', x)).join(', ');
    }
    if (o.length && o.every(x => x && typeof x === 'object' && 'url' in x && ('width' in x || 'type' in x) && Object.keys(x).length <= 5 && /\.(jpe?g|png|webp)/i.test(x.url||''))) {
      return '<div class="thumbs">' + o.map(x => fmtVal('', x.url)).join('') + '</div>';
    }
    return o.map(x => `<div class="item">${renderObj(x, depth+1)}</div>`).join('');
  }
  const rows = [];
  for (const [k, v] of Object.entries(o)) {
    if (SKIP.has(k) || isEmpty(v) || lab(k) === '') continue;
    rows.push(`<tr><td class="k">${esc(lab(k))}</td><td>${(v && typeof v === 'object') ? renderObj(v, depth+1) : fmtVal(k, v)}</td></tr>`);
  }
  return rows.length ? `<table class="kv">${rows.join('')}</table>` : '<span class="hint">нет данных</span>';
}

// ---------- Интерфейс выбора ----------
let kind = 'vin';
function detect(raw){
  const s = raw.trim().toUpperCase().replace(/\s+/g,'');
  if (!s) return null;
  const lat = s.replace(/[АВЕКМНОРСТУХ]/g, c => 'ABEKMHOPCTYX'['АВЕКМНОРСТУХ'.indexOf(c)]);
  if (/^[ABEKMHOPCTYX]\d{3}[ABEKMHOPCTYX]{2}\d{2,3}$/.test(lat)) return {kind:'plate', value:s};
  if (/^[A-HJ-NPR-Z0-9]{17}$/.test(s)) return {kind:'vin', value:s};
  if (/^[A-Z0-9-]{5,20}$/.test(s)) return {kind:'body', value:s};
  return {kind:'bad', value:s};
}
function buildChecks(){
  let html = '';
  const saved = loadSel();
  for (const [g, gt] of GROUPS) {
    html += `<div class="gtitle">${gt}</div>`;
    for (const c of CHECKS.filter(c => c.g === g)) {
      const on = saved ? saved.includes(c.id) : !!c.base;
      html += `<label class="ck" data-id="${c.id}"><input type="checkbox" value="${c.id}" ${on?'checked':''}><span>${esc(c.t)} <span class="hint" data-p></span></span><span class="pr">${money(c.price)}</span></label>`;
    }
  }
  $('#checks').innerHTML = html;
  $('#checks').addEventListener('change', () => { saveSel(); updateUI(); });
}
function selected(){ return [...document.querySelectorAll('#checks input:checked')].map(i => CHECKS.find(c => c.id === i.value)); }
function loadSel(){ try { return JSON.parse(localStorage.getItem('avcSel')); } catch(e){ return null; } }
function saveSel(){ try { localStorage.setItem('avcSel', JSON.stringify(selected().map(c => c.id))); } catch(e){} }

function supportsKind(c, k){ return c.p.includes(k) || (k === 'plate' && c.p.includes('vin')); }

function updateUI(){
  const d = detect($('#q').value);
  kind = d && d.kind !== 'bad' ? d.kind : (d ? 'bad' : null);
  const kEl = $('#kind'), hint = $('#kindHint');
  if (!d) { kEl.textContent = 'введите данные'; hint.textContent = 'Тип определится сам: 17 символов — VIN, А123ВС38 — госномер, остальное — номер кузова'; }
  else if (d.kind === 'bad') { kEl.textContent = 'не распознано'; hint.textContent = 'Допустимы латиница, цифры и дефис; в VIN нет букв I, O, Q'; }
  else {
    kEl.textContent = KIND_RU[d.kind];
    hint.textContent = d.kind === 'plate' ? 'Для проверок только по VIN программа сначала узнает VIN по госномеру (+8 ₽)'
      : d.kind === 'body' ? 'Проверки, которые работают только по VIN, будут пропущены' : '';
  }
  let sum = 0, needResolve = false;
  for (const lb of document.querySelectorAll('#checks label.ck')) {
    const c = CHECKS.find(x => x.id === lb.dataset.id);
    const ok = !d || d.kind === 'bad' || supportsKind(c, d.kind);
    lb.classList.toggle('na', !ok);
    lb.querySelector('[data-p]').textContent = ok ? '' : '(только по VIN)';
    if (lb.querySelector('input').checked && ok) {
      sum += c.price;
      if (d && d.kind === 'plate' && !c.p.includes('plate')) needResolve = true;
    }
  }
  if (needResolve) sum += 8;
  $('#total').textContent = money(sum);
}
$('#q').addEventListener('input', updateUI);
document.querySelector('.presets').addEventListener('click', e => {
  const p = e.target.dataset.preset; if (!p) return;
  for (const i of document.querySelectorAll('#checks input')) {
    const c = CHECKS.find(x => x.id === i.value);
    i.checked = p === 'all' ? true : p === 'none' ? false : p === 'base' ? !!c.base : c.g !== 'foreign';
  }
  saveSel(); updateUI();
});

// ---------- Связь с локальной программой ----------
async function api(ep, params){
  const qs = new URLSearchParams(params).toString();
  const r = await fetch(`/api/${ep}?${qs}`);
  let data; const txt = await r.text();
  try { data = JSON.parse(txt); } catch(e) { data = {success:0, error:'Некорректный ответ сервера: ' + txt.slice(0,200)}; }
  data.__http = r.status;
  return data;
}
async function refreshBalance(){
  try {
    const d = await api('balance', {});
    if (d.success) {
      let s = money(d.balance);
      if (d.nearestExpiry && d.nearestExpiry.amount) s += ` <span class="hint">(${money(d.nearestExpiry.amount)} сгорит ${fmtVal('', d.nearestExpiry.date)})</span>`;
      $('#bal').innerHTML = s;
    } else $('#bal').textContent = d.code === 'NO_TOKEN' || d.code === 'TOKEN_INVALID' || d.code === 'LOCAL_NO_TOKEN' ? 'нет токена' : (d.error || 'ошибка');
  } catch(e){ $('#bal').textContent = 'программа не запущена'; }
}
$('#refreshBal').onclick = refreshBalance;

// токен
function openTok(){ $('#tokModal').classList.add('on'); $('#tokIn').value=''; $('#tokMsg').textContent=''; setTimeout(()=>$('#tokIn').focus(), 50); }
$('#tokenBtn').onclick = openTok;
$('#tokCancel').onclick = () => $('#tokModal').classList.remove('on');
$('#tokSave').onclick = async () => {
  const t = $('#tokIn').value.trim();
  if (!/^[0-9a-fA-F]{96}$/.test(t)) { $('#tokMsg').textContent = 'Токен должен быть из 96 символов 0-9 и a-f'; return; }
  const r = await fetch('/local/token', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({token:t})});
  if (r.ok) { $('#tokModal').classList.remove('on'); refreshBalance(); } else $('#tokMsg').textContent = 'Не удалось сохранить';
};

// ---------- Запуск проверок ----------
const sleep = ms => new Promise(r => setTimeout(r, ms));
let lastRun = null;

function cardHTML(c){
  return `<details class="res" id="r-${c.id}"><summary><span class="st run">в работе…</span><span class="nm">${esc(c.t)}</span><span class="sm"></span></summary><div class="body"></div></details>`;
}
function setCard(id, cls, stText, sm, body, open){
  const el = document.getElementById('r-' + id); if (!el) return;
  const st = el.querySelector('.st'); st.className = 'st ' + cls; st.textContent = stText;
  el.querySelector('.sm').innerHTML = sm || '';
  if (body !== undefined) el.querySelector('.body').innerHTML = body;
  if (open) el.open = true;
}

async function runOne(c, ids, testMode){
  let k = c.p.find(x => ids[x]);
  if (!k) { setCard(c.id, 'none', 'пропущено', 'нужен ' + c.p.map(x => KIND_RU[x]).join(' или '), ''); return {c, skipped:true}; }
  const ep = (c.ep && c.ep[k]) || c.id;
  const params = {}; params[k] = ids[k];
  let d = await api(ep, params);
  let charged = (d.billing && +d.billing.charged) || 0;
  // асинхронные проверки: ждём готовности
  const t0 = Date.now();
  while (d.success && d.status === 'pending' && d.taskId) {
    const maxWait = (d.maxWaitSec || 900) * 1000;
    if (Date.now() - t0 > maxWait) { d = {success:0, error:'Отчёт готовится дольше обычного. Номер задачи: ' + d.taskId, code:'TIMEOUT', taskId:d.taskId}; break; }
    setCard(c.id, 'run', 'готовится…', d.etaSec ? `осталось ~${d.etaSec} с` : '', '');
    await sleep(Math.max(2, d.pollAfterSec || 5) * 1000);
    const tid = d.taskId;
    d = await api(ep, {task: tid});
    if (!d.taskId && d.status === 'pending') d.taskId = tid;
    charged += (d.billing && +d.billing.charged) || 0;
  }
  return {c, d, charged, by:k};
}

function judge(c, d){
  // возвращает [класс, текст статуса, краткая сводка]
  if (!d.success) {
    const nf = ['NOT_FOUND'].includes(d.code);
    const notConn = ['NOT_ALLOWED','SCORE_NOT_ALLOWED','API_DISABLED'].includes(d.code);
    return [nf ? 'none' : notConn ? 'none' : 'err', nf ? 'нет данных' : notConn ? 'не подключено' : 'ошибка', esc(d.error || 'Источник не вернул данные (без списания)')];
  }
  const f = d.found;
  const none = (f === 0 || f === false);
  switch (c.id) {
    case 'score': {
      if (!d.record) return ['none','нет в базе', esc(d.message || 'Не найден в базе ГИБДД')];
      const s = d.status || {}; const own = (d.record.ownershipPeriods||[]).length;
      if (s.wanted || s.spec_wanted) return ['err','РОЗЫСК', 'Автомобиль в розыске!'];
      if (s.restricted) return ['err','ограничения', `Ограничений: ${(d.restrictions||[]).length} · владельцев: ${own}`];
      return ['ok','чисто', `Без ограничений · владельцев: ${own}`];
    }
    case 'gibdd': case 'gibdd-archive': {
      if (!d.record) return ['none','нет данных', esc(d.message||'')];
      return ['ok','найдено', `Владельцев: ${(d.record.ownershipPeriods||[]).length} · ${esc(d.record.model||'')} ${esc(d.record.year||'')}`];
    }
    case 'pledge': return d.active_count ? ['err','В ЗАЛОГЕ', `Активных залогов: ${d.active_count}`] : none ? ['ok','чисто','Залогов нет'] : ['warn','были залоги', `Записей: ${f}, активных нет`];
    case 'lizing': return d.active ? ['err','в лизинге', 'Действующий договор лизинга'] : d.isLeasing ? ['warn','был в лизинге', `Договоров: ${f}, действующих нет`] : ['ok','чисто','Лизинга нет'];
    case 'accidents': case 'accidents-rt': return (d.hasAccidents || f > 0) ? ['warn','ДТП', `ДТП: ${(d.records||[]).length || f}`] : ['ok','нет ДТП', 'ДТП не найдено'];
    case 'hidden-damage': return f > 0 ? ['warn','найдено', Object.entries(d.summary||{}).filter(([,v])=>v).map(([k,v]) => `${lab(k)}: ${v}`).join(' · ')] : ['ok','чисто','Ничего не найдено'];
    case 'taxi': return d.isTaxi ? ['warn','ТАКСИ', `Разрешений: ${(d.records||[]).length}` + ((d.records||[]).some(r=>r.isActual) ? ' (есть действующее)' : '')] : ['ok','нет','В такси не работал'];
    case 'sharing': return d.isCarsharing ? ['warn','каршеринг', esc(d.company || 'Был в каршеринге')] : ['ok','нет','Не каршеринг'];
    case 'lawsuits': return (d.count || f) > 0 ? ['warn','есть дела', `Дел: ${d.count || f}`] : ['ok','нет','Судебных дел нет'];
    case 'probeg': {
      const rec = (d.records||[]).filter(r => r.car_mileage).sort((a,b) => String(a.date_of_diagnosis).localeCompare(String(b.date_of_diagnosis)));
      if (!rec.length) return ['none','нет данных','Техосмотров не найдено'];
      let roll = false; for (let i=1;i<rec.length;i++) if (+rec[i].car_mileage < +rec[i-1].car_mileage) roll = true;
      const last = rec[rec.length-1];
      return [roll ? 'err' : 'ok', roll ? 'СКРУТКА?' : 'найдено', `Последний пробег ${(+last.car_mileage).toLocaleString('ru-RU')} км (${fmtVal('',last.date_of_diagnosis)})` + (roll ? ' · пробег уменьшался!' : '')];
    }
    case 'recalls': return none ? ['ok','нет','Отзывных кампаний нет'] : ['warn','есть', `Кампаний: ${(d.records||[]).length}`];
    case 'price': return d.price ? ['ok','оценка', `Средняя ${fmtVal('price', d.price.average)} (${fmtVal('price', d.price.min)} – ${fmtVal('price', d.price.max)})`] : ['none','нет данных',''];
    case 'customs': case 'customs-fts': {
      if (none) return ['none','нет данных','Таможенных данных нет'];
      const r = (d.records||[])[0] || {}; const fee = (r.recyclingFee||[])[0];
      return ['ok','найдено', `Выпуск ${fmtVal('', r.releaseDate)}${r.country ? ' · ' + esc(r.country) : ''}${fee ? ' · утильсбор: ' + esc(fee.paymentStatus) : ''}`];
    }
    case 'decode': { const v = (d.variants||[])[0]; return v ? ['ok','расшифрован', esc(v.title)] : ['none','нет данных','']; }
    case 'brief': return d.response ? ['ok','найдено', esc(d.response.mark_model + ' ' + (d.response.year||''))] : ['none','нет данных',''];
    case 'vin2gos': return d.licensePlate ? ['ok','найдено', esc(d.licensePlate)] : ['none','нет данных',''];
    case 'plate-history': return (d.plates||[]).length ? ['ok','найдено', esc(d.plates.join(', '))] : ['none','нет данных',''];
    case 'autopark': return d.engineNumber ? ['ok','найдено', 'Двигатель ' + esc(d.engineNumber)] : ['none','нет данных',''];
    case 'osago': { const p = (d.policies||[]); return p.length ? ['ok','найдено', esc(p[0].companyName + ' · ' + p[0].status)] : ['none','нет полисов','']; }
    case 'offers': return (d.records||[]).length ? ['ok','найдено', `Объявлений: ${d.records.length}`] : ['none','нет','Объявлений нет'];
    case 'nomerogram': return d.totalPhotos ? ['ok','найдено', `Фото: ${d.totalPhotos}`] : ['none','нет фото',''];
    case 'service': return (d.records||[]).length ? ['ok','найдено', `Записей: ${d.records.length}`] : ['none','нет данных',''];
    case 'elpts': { const r=(d.records||[])[0]; return r ? ['ok','найдено', esc(`Ограничения: ${r.restrictions_status||'—'} · утильсбор: ${r.displosal_fee||'—'}`)] : ['none','нет данных','']; }
    case 'vin-precheck': { const a = (d.items||[]).filter(i => i.available); return a.length ? ['ok','есть данные', esc(a.map(i => i.title).join(' · '))] : ['none','нет данных','В иностранных базах не найдено']; }
    default:
      if (d.report) return ['ok','готово', esc(d.report.title || 'Отчёт готов')];
      return none ? ['none','нет данных',''] : ['ok','найдено',''];
  }
}

function bodyHTML(c, d){
  if (!d.success) return d.taskId ? `<div class="hint">Номер задачи: <code>${esc(d.taskId)}</code></div>` : '';
  if (d.report) {
    const r = d.report;
    let h = '';
    const files = (r.files||[]).map(f => `<a href="${esc(f.url)}" target="_blank" rel="noopener">${esc(f.name)}</a> <span class="hint">(${f.type.toUpperCase()})</span>`).join('<br>');
    if (r.web_url) h += `<p><a href="${esc(r.web_url)}" target="_blank" rel="noopener"><b>Открыть отчёт</b></a></p>`;
    if (files) h += `<p>${files}</p>`;
    if (r.files_until) h += `<p class="hint">Файлы доступны до ${fmtVal('', r.files_until)}</p>`;
    if (r.data) {
      const {vehicle, summary, score} = r.data;
      const top = {}; if (vehicle) top.vehicle = Object.fromEntries(Object.entries(vehicle).filter(([k]) => !/_en$|facts/.test(k)));
      if (summary) top.summary = Object.fromEntries(Object.entries(summary).filter(([k]) => !/_en$/.test(k)));
      if (score) top.score = score;
      h += renderObj(top);
      h += `<details style="margin-top:8px"><summary class="hint" style="cursor:pointer">Все данные отчёта</summary>${renderObj(r.data)}</details>`;
    }
    return h;
  }
  const copy = Object.assign({}, d); delete copy.__http;
  return renderObj(copy);
}

async function run(testMode){
  const d0 = detect($('#q').value);
  let ids = {};
  if (testMode) {
    const k = d0 && d0.kind !== 'bad' ? d0.kind : 'vin';
    ids[k] = TEST[k];
  } else {
    if (!d0 || d0.kind === 'bad') { updateUI(); $('#q').focus(); return; }
    ids[d0.kind] = d0.value;
  }
  const inKind = Object.keys(ids)[0];
  const list = selected();
  if (!list.length) { alertBox('Отметьте хотя бы одну проверку'); return; }
  const sum = list.filter(c => supportsKind(c, inKind)).reduce((a,c) => a + c.price, 0);
  if (!testMode && sum >= 300 && !await confirmBox(`Выбраны дорогие отчёты, примерно ${money(sum)}. Продолжить?`)) return;

  $('#go').disabled = $('#test').disabled = true;
  $('#report').style.display = '';
  $('#rTitle').textContent = `${KIND_RU[inKind]}: ${ids[inKind]}`;
  $('#rSub').textContent = 'Проверка от ' + new Date().toLocaleString('ru-RU');
  $('#testBanner').innerHTML = testMode ? '<div class="banner">Тестовый режим: вымышленные данные, деньги не списываются.</div>' : '';
  $('#flags').innerHTML = '';
  const results = [];
  const resolveNeeded = inKind === 'plate' && list.some(c => !c.p.includes('plate'));
  const cards = (resolveNeeded ? [{id:'gos2vin', t:'VIN и кузов по госномеру', p:['plate']}] : []).concat(list);
  $('#results').innerHTML = cards.map(cardHTML).join('');

  let totalCharged = 0;
  if (resolveNeeded) {
    const g = await api('gos2vin', {plate: ids.plate});
    const ch = (g.billing && +g.billing.charged) || 0; totalCharged += ch;
    if (g.success && (g.vin || g.bodyNumber)) {
      if (g.vin) ids.vin = g.vin; if (g.bodyNumber) ids.body = g.bodyNumber;
      setCard('gos2vin', 'ok', 'найдено', esc([g.vin, g.bodyNumber, g.brand, g.model, g.year].filter(Boolean).join(' · ')) + (ch ? ` · ${money(ch)}` : ''), renderObj(g));
      $('#rTitle').textContent = `Госномер: ${ids.plate}` + (g.vin ? ` · VIN ${g.vin}` : '') + (g.brand ? ` · ${g.brand} ${g.model||''} ${g.year||''}` : '');
    } else {
      setCard('gos2vin', 'err', 'не найдено', esc(g.error || 'VIN по госномеру не найден'), '');
    }
    results.push({c:{id:'gos2vin', t:'VIN по госномеру'}, d:g, charged:ch});
  }

  // параллельно по 4
  const queue = list.slice();
  async function worker(){
    while (queue.length) {
      const c = queue.shift();
      let res;
      try { res = await runOne(c, ids, testMode); }
      catch(e){ res = {c, d:{success:0, error:'Нет связи с программой: ' + e.message}, charged:0}; }
      if (!res.skipped) {
        const [cls, st, sm] = judge(c, res.d);
        const extra = res.charged ? ` · <b>${money(res.charged)}</b>` : '';
        setCard(c.id, cls, st, sm + extra, bodyHTML(c, res.d), cls === 'err' || cls === 'warn');
        totalCharged += res.charged;
        res.verdict = [cls, st, sm];
        if (!ids.vin && res.d && res.d.record && res.d.record.vin && /^[A-HJ-NPR-Z0-9]{17}$/.test(res.d.record.vin)) ids.vin = res.d.record.vin;
      }
      results.push(res);
      renderFlags(results, totalCharged, testMode);
    }
  }
  await Promise.all([worker(), worker(), worker(), worker()]);
  renderFlags(results, totalCharged, testMode, true);
  lastRun = {ids, inKind, results, totalCharged, testMode, when: new Date()};
  $('#go').disabled = $('#test').disabled = false;
  refreshBalance();
}

function renderFlags(results, total, testMode, done){
  const fl = [];
  for (const r of results) {
    if (!r.verdict) continue;
    const [cls, st, sm] = r.verdict;
    if (cls === 'err' || cls === 'warn') fl.push(`<span class="flag ${cls}">${esc(r.c.t)}: ${sm.replace(/<[^>]+>/g,'')}</span>`);
  }
  const okCount = results.filter(r => r.verdict && r.verdict[0] === 'ok').length;
  if (done && !fl.length && okCount) fl.push('<span class="flag ok">Проблем не найдено</span>');
  fl.push(`<span class="flag" style="background:#f1f2f4">Списано: <b>${money(total)}</b>${testMode ? ' (тест)' : ''}${done ? '' : ' · идёт проверка…'}</span>`);
  $('#flags').innerHTML = fl.join('');
}

// ---------- Отчёт: копирование, сохранение ----------
function reportText(){
  if (!lastRun) return '';
  const lines = [$('#rTitle').textContent, $('#rSub').textContent, ''];
  for (const r of lastRun.results) {
    if (r.skipped) continue;
    const v = r.verdict || judge(r.c, r.d);
    lines.push(`• ${r.c.t}: ${v[1]}${v[2] ? ' — ' + v[2].replace(/<[^>]+>/g,'') : ''}`);
  }
  lines.push('', 'Списано: ' + money(lastRun.totalCharged));
  return lines.join('\n');
}
$('#copy').onclick = async () => {
  try { await navigator.clipboard.writeText(reportText()); $('#copy').textContent = 'Скопировано ✓'; }
  catch(e){ $('#copy').textContent = 'Не удалось'; }
  setTimeout(() => $('#copy').textContent = 'Скопировать текстом', 1800);
};
$('#save').onclick = () => {
  document.querySelectorAll('#results details.res').forEach(d => d.open = true);
  const css = document.querySelector('style').outerHTML;
  const html = `<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8"><title>${esc($('#rTitle').textContent)}</title>${css}</head><body><div class="wrap">${document.getElementById('report').innerHTML.replace(/<div class="row noprint">[\s\S]*?<\/div>/,'')}</div></body></html>`;
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([html], {type:'text/html'}));
  const id = (lastRun && lastRun.ids[lastRun.inKind] || 'auto').replace(/[^\wА-Яа-я-]/g,'');
  a.download = `Проверка_${id}_${new Date().toISOString().slice(0,10)}.html`;
  a.click();
};
$('#print').onclick = () => { document.querySelectorAll('#results details.res').forEach(d => d.open = true); window.print(); };
$('#expand').onclick = () => { const all = [...document.querySelectorAll('#results details.res')]; const open = all.some(d => !d.open); all.forEach(d => d.open = open); };

// простые диалоги внутри страницы
function confirmBox(text){
  return new Promise(res => {
    const m = document.createElement('div'); m.className = 'modal on';
    m.innerHTML = `<div class="card"><p>${esc(text)}</p><div class="row"><button data-y>Да, проверить</button><button class="sec" data-n>Отмена</button></div></div>`;
    document.body.appendChild(m);
    m.querySelector('[data-y]').onclick = () => { m.remove(); res(true); };
    m.querySelector('[data-n]').onclick = () => { m.remove(); res(false); };
  });
}
function alertBox(text){
  const m = document.createElement('div'); m.className = 'modal on';
  m.innerHTML = `<div class="card"><p>${esc(text)}</p><button>OK</button></div>`;
  document.body.appendChild(m); m.querySelector('button').onclick = () => m.remove();
}

$('#f').addEventListener('submit', e => { e.preventDefault(); run(false); });
$('#test').onclick = () => run(true);

// старт
buildChecks(); updateUI();
fetch('/local/token-status').then(r => r.json()).then(s => { if (!s.set) openTok(); else refreshBalance(); }).catch(() => { $('#bal').textContent = 'программа не запущена'; });
</script>
</body>
</html>
'''


def read_token():
    try:
        with open(TOKEN_FILE, encoding='utf-8') as f:
            return f.read().strip()
    except OSError:
        return ''


class Handler(BaseHTTPRequestHandler):
    server_version = 'AvtoVinCodLocal/1.0'

    def log_message(self, fmt, *args):
        pass  # не засоряем окно

    def _send(self, code, body, ctype='application/json; charset=utf-8'):
        data = body.encode('utf-8') if isinstance(body, str) else body
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)

    def _local_only(self):
        host = (self.headers.get('Host') or '').split(':')[0]
        if host not in ('127.0.0.1', 'localhost'):
            self._send(403, json.dumps({'success': 0, 'error': 'forbidden'}))
            return False
        return True

    def do_GET(self):
        if not self._local_only():
            return
        url = urllib.parse.urlsplit(self.path)
        if url.path in ('/', '/index.html'):
            return self._send(200, PAGE, 'text/html; charset=utf-8')
        if url.path == '/local/token-status':
            return self._send(200, json.dumps({'set': bool(read_token())}))
        if url.path.startswith('/api/'):
            return self._proxy(url.path[5:], url.query)
        self._send(404, json.dumps({'success': 0, 'error': 'not found'}))

    def do_POST(self):
        if not self._local_only():
            return
        if self.path == '/local/token':
            try:
                n = int(self.headers.get('Content-Length') or 0)
                tok = json.loads(self.rfile.read(n).decode('utf-8')).get('token', '').strip()
                if len(tok) != 96 or any(c not in '0123456789abcdefABCDEF' for c in tok):
                    raise ValueError
                with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
                    f.write(tok)
                return self._send(200, json.dumps({'ok': 1}))
            except Exception:
                return self._send(400, json.dumps({'ok': 0}))
        self._send(404, json.dumps({'success': 0, 'error': 'not found'}))

    def _proxy(self, ep, query):
        if ep not in ALLOWED:
            return self._send(400, json.dumps({'success': 0, 'error': 'Неизвестная проверка', 'code': 'LOCAL_BAD_EP'}, ensure_ascii=False))
        token = read_token()
        if not token:
            return self._send(401, json.dumps({'success': 0, 'error': 'Токен не задан. Нажмите «Токен» вверху страницы.', 'code': 'LOCAL_NO_TOKEN'}, ensure_ascii=False))
        target = BASE + '/' + ep + ('?' + query if query else '')
        req = urllib.request.Request(target, headers={
            'Authorization': 'Bearer ' + token,
            'Accept': 'application/json',
            'User-Agent': 'AvtoVinCod-local-checker/1.0',
        })
        try:
            with urllib.request.urlopen(req, timeout=130) as r:
                return self._send(r.status, r.read())
        except urllib.error.HTTPError as e:
            body = e.read() or json.dumps({'success': 0, 'error': 'HTTP %d' % e.code}).encode()
            return self._send(e.code, body)
        except Exception as e:  # нет интернета, таймаут и т.п.
            msg = 'Нет связи с api.avtovincod.ru (%s). Проверьте интернет.' % e.__class__.__name__
            return self._send(502, json.dumps({'success': 0, 'error': msg, 'code': 'LOCAL_NET'}, ensure_ascii=False))


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    port = PORT
    server = None
    for p in range(PORT, PORT + 20):
        try:
            server = ThreadingHTTPServer(('127.0.0.1', p), Handler)
            port = p
            break
        except OSError:
            continue
    if server is None:
        print('Не удалось занять порт. Закройте другие копии программы.')
        input('Нажмите Enter...')
        return
    url = 'http://127.0.0.1:%d/' % port
    print('Программа проверки авто запущена: ' + url)
    print('Страница откроется в браузере. Не закрывайте это окно, пока работаете.')
    print('Чтобы выйти — закройте окно или нажмите Ctrl+C.')
    if '--no-browser' not in sys.argv:
        threading.Timer(0.7, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
