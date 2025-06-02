let knownCompanies = [];
let isNewCustomer = false;
let selectedTransportType = null;
let preferredAlt = null;

fetch('https://bbus-project.onrender.com/api/companies')
  .then(response => response.json())
  .then(companies => {
    knownCompanies = companies;
  });

const input = document.getElementById('company-input');
const suggestions = document.getElementById('company-suggestions');
const newCompanyBlock = document.getElementById('new-company-block');
const newCompanyInput = document.getElementById('new-company-name');

input.addEventListener('input', filterCompanies);
input.addEventListener('focus', showAllCompanies);
document.addEventListener('click', e => {
  if (!e.target.closest('.company-list')) {
    suggestions.style.display = 'none';
  }
});

document.getElementById('price').addEventListener('input', updateTotalPrice);
document.getElementById('hours').addEventListener('input', updateTotalPrice);
document.getElementById('passengers').addEventListener('input', () => {
  validatePassengers(document.getElementById('passengers'));
});

function submitNotifyRequest(type, inputId) {
  const contact = document.getElementById(inputId).value;
  if (!contact.trim()) {
    alert("Пожалуйста, укажите контакт клиента для связи.");
    document.getElementById(inputId).parentElement.remove();
    return;
  }

  const company = input.value;
  const datetimeStr = document.getElementById("booking_datetime").value;

  fetch('https://bbus-project.onrender.com/api/notify_request', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      company,
      vehicle_type: type,
      desired_time: datetimeStr,
      contact
    })
  })
    .then(response => response.json())
    .then(() => alert("Контакт сохранен. Выберите другое ТС."))
    .catch(err => alert(`Ошибка при отправке запроса: ${err.message}`));
}

function markPreferredNotification(type) {
  preferredAlt = type;
  const box = document.querySelector(".recommendations-box");
  const contactInputId = `notify-contact-${type.replace(/\s+/g, '-')}`;

  // Удалить предыдущую форму, если уже существует
  const existingForm = document.querySelector(".notify-form");
  if (existingForm) existingForm.remove();

  const form = document.createElement("div");
  form.classList.add("notify-form");
  form.style.marginTop = "15px";
  form.style.border = "1px solid #ccc";
  form.style.padding = "15px";
  form.style.borderRadius = "5px";
  form.style.backgroundColor = "#fefefe";

  form.innerHTML = `
    <p style="margin-bottom: 8px;"><strong>Транспорт ${type}</strong> сейчас занят. Оставьте контакт клиента для уведомления:</p>
    <input type="text" id="${contactInputId}" placeholder="Телефон или Email" style="width: 100%; padding: 8px; margin-bottom: 10px;">
    <div style="display: flex; gap: 10px;">
      <button class="custom-btn" onclick="submitNotifyRequest('${type}', '${contactInputId}')">Отправить</button>
      <button class="custom-btn" onclick="saveWithoutTransport('${type}', '${contactInputId}')">Сохранить заказ без выбора ТС</button>
    </div>
  `;

  box.appendChild(form);
}

function updateTotalPrice() {
  const price = parseFloat(document.getElementById('price').value);
  const hours = parseFloat(document.getElementById('hours').value);
  const summary = document.getElementById('price-summary');
  if (!isNaN(price) && !isNaN(hours)) {
    summary.textContent = `К оплате: ${Math.round(price * hours)} руб.`;
  } else {
    summary.textContent = 'К оплате: —';
  }
}

function filterCompanies() {
  const value = input.value.toLowerCase();
  const filtered = knownCompanies.filter(name => name.toLowerCase().includes(value));
  renderCompanySuggestions(filtered);
}

function showAllCompanies() {
  renderCompanySuggestions(knownCompanies);
}

function renderCompanySuggestions(companies) {
  suggestions.innerHTML = '';
  companies.forEach(company => {
    const div = document.createElement('div');
    div.textContent = company;
    div.onclick = () => selectCompany(company);
    suggestions.appendChild(div);
  });

  const value = input.value.toLowerCase();
  if (value && !knownCompanies.some(name => name.toLowerCase() === value)) {
    const div = document.createElement('div');
    div.textContent = 'Новый заказчик';
    div.style.fontWeight = 'bold';
    div.style.color = '#800000';
    div.onclick = () => selectCompany('Новый заказчик');
    suggestions.appendChild(div);
  }
  suggestions.style.display = 'block';
}

function selectCompany(name) {
  input.value = name;
  suggestions.style.display = 'none';
  isNewCustomer = name === 'Новый заказчик';
  newCompanyBlock.style.display = isNewCustomer ? 'block' : 'none';

  const preferencesBox = document.querySelector('.preferences-box');
  const recommendationsBox = document.querySelector('.recommendations-box');
  const historyTable = document.querySelector('.table-box tbody');

  if (isNewCustomer) {
    preferencesBox.innerHTML = '<div class="section-title">Предпочтения клиента</div><p>Нет данных для нового заказчика</p>';
    recommendationsBox.innerHTML = '<div class="section-title">Рекомендованные типы ТС</div><p>Нет данных</p>';
    historyTable.innerHTML = '<tr><td colspan="7">История заказов отсутствует</td></tr>';
    return;
  }

  fetch(`https://bbus-project.onrender.com/api/customer_profile/${encodeURIComponent(name)}`)
    .then(response => response.json())
    .then(profile => {
      if (profile.error) {
        preferencesBox.innerHTML = '<div class="section-title">Предпочтения клиента</div><p>Нет данных по заказчику</p>';
      } else {
        preferencesBox.innerHTML = `
          <div class="section-title">Предпочтения клиента</div>
          <p><strong>Любимый тип ТС:</strong> ${profile.любимый_тип_тс}</p>
          <p><strong>Любимая модель ТС:</strong> ${profile.исторический_любимый_тс}</p>
          <p><strong>Любимый статус заказа:</strong> ${profile.любимый_статус_заказа}</p>
          <p><strong>Среднее количество пассажиров:</strong> ${profile.среднее_пассажиров.toFixed(1)}</p>
          <p><strong>Всего заказов:</strong> ${profile.всего_заказов}</p>
        `;
      }
    });

  fetch(`https://bbus-project.onrender.com/api/history/${encodeURIComponent(name)}`)
    .then(response => response.json())
    .then(data => {
      const rows = data.length ? data.map(row => `
        <tr>
          <td>${row.дата}</td>
          <td>${row.тип_тс}</td>
          <td>${row.пассажиров}</td>
          <td>${row.цена}</td>
          <td>${row.тип}</td>
          <td>${row.статус}</td>
          <td>${row.маршрут}</td>
        </tr>`).join('') : '<tr><td colspan="7">История заказов отсутствует</td></tr>';
      historyTable.innerHTML = rows;
    });
}

function validatePassengers(input) {
  const warning = document.getElementById('passenger-warning');
  const value = parseInt(input.value);
  if (value < 1 || value > 59) {
    warning.style.display = 'block';
  } else {
    warning.style.display = 'none';
  }
}

document.getElementById('submit-button').onclick = function (e) {
  e.preventDefault();

  const company = input.value.trim();
  const status = document.getElementById('status').value;
  const passengers = parseInt(document.getElementById('passengers').value);
  const pricePerHour = parseFloat(document.getElementById('price').value);
  const hours = parseFloat(document.getElementById('hours').value);
  const routeFrom = document.getElementById('route-from').value.trim();
  const routeTo = document.getElementById('route-to').value.trim();

  // Проверки
  if (!company) {
    alert('Укажите компанию.');
    return;
  }
  if (isNaN(passengers) || passengers < 1 || passengers > 59) {
    alert('Количество пассажиров должно быть от 1 до 59.');
    return;
  }
  if (isNaN(pricePerHour) || pricePerHour <= 0) {
    alert('Стоимость за час должна быть положительным числом.');
    return;
  }
  if (isNaN(hours) || hours < 1) {
    alert('Количество часов аренды должно быть не менее 1 часа.');
    return;
  }
  if (!routeFrom || !routeTo) {
    alert('Маршрут "ОТ" и "ДО" обязательны для заполнения.');
    return;
  }

  const datetimeStr = document.getElementById("booking_datetime").value;
  let booking_start = "";
  let booking_end = "";

  if (datetimeStr && !isNaN(hours)) {
    const [datePart, timePart] = datetimeStr.split(' ');
    const [yyyy, mm, dd] = datePart.split('-').map(Number);
    const [hh, min, ss] = timePart.split(':').map(Number);
    const start = new Date(yyyy, mm - 1, dd, hh, min, ss);
    const end = new Date(start.getTime() + hours * 60 * 60 * 1000);

    const pad = n => n.toString().padStart(2, '0');
    const format = dt => `${dt.getFullYear()}-${pad(dt.getMonth() + 1)}-${pad(dt.getDate())} ${pad(dt.getHours())}:${pad(dt.getMinutes())}:${pad(dt.getSeconds())}`;
    booking_start = format(start);
    booking_end = format(end);
  }

  fetch('https://bbus-project.onrender.com/api/recommend', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      company,
      passengers,
      price: pricePerHour,
      status,
      booking_start,
      booking_end
    })
  })
    .then(response => response.json())
    .then(recommendations => {
      const box = document.querySelector('.recommendations-box');
      let html = '<div class="section-title">Рекомендованные типы ТС</div>';
      html += '<div style="max-height: 300px; overflow-y: auto; padding-right: 10px;">';
      if (!recommendations.length) {
        html += '<p>Не удалось найти подходящий транспорт по количеству пассажиров.</p>';
      } else {
        recommendations.forEach(rec => {
          const tag = rec.preferred
            ? rec.valid_capacity
              ? ' <span style="color: green;">(Предпочтение)</span>'
              : ' <span style="color: orange;">(Предпочтение, вместимость не подходит)</span>'
            : '';

          const style = rec.preferred ? 'border: 2px solid #800000; padding: 10px;' : '';

          if (!rec.available) {
            html += `
              <div class="recommendation" style="${style}">
                <p><strong>${rec.type}</strong>: <span style="color: red;">Занят на данное время бронирования</span><br>
                (вместимость: ${rec.capacity} мест)${tag}</p>
                <button class="select-btn custom-btn" onclick="markPreferredNotification('${rec.type}')">Сообщить, если освободится</button>
              </div>`;
          } else {
            html += `
              <div class="recommendation" style="${style}">
                <p><strong>${rec.type}</strong>${tag} (вместимость: ${rec.capacity} мест)</p>
                <p>Вероятность: ${(rec.probability * 100).toFixed(1)}%</p>
                <button class="select-btn custom-btn" onclick="selectTransport('${rec.type}')">Выбрать</button>
              </div>`;
          }
        });
        html += '</div>';
        if (!recommendations.some(r => r.available)) {
          html += `<div style="margin-top: 20px; background-color: #fff0f0; padding: 10px; border-left: 4px solid #800000; color: #800000; font-weight: bold;">
            Все подходящие ТС заняты. Рассмотрите возможность разделения пассажиров на несколько ТС.
          </div>`;
        }
        html += `<p id="selected-transport-msg" style="margin-top: 10px; font-weight: bold; color: green;"></p>`;
      }
      box.innerHTML = html;
    });
};

function selectTransport(type) {
  selectedTransportType = type;
  const msg = document.getElementById("selected-transport-msg");
  if (msg) {
    msg.textContent = `Вы выбрали: ${type}`;
  }

  // Данные из формы
  const company = input.value;
  const passengers = parseInt(document.getElementById('passengers').value);
  const pricePerHour = parseFloat(document.getElementById('price').value);
  const hours = parseFloat(document.getElementById('hours').value);
  const status = document.getElementById('status').value;
  const newCompanyName = newCompanyInput.value;
  const datetimeStr = document.getElementById("booking_datetime").value;
  const routeFrom = document.getElementById('route-from').value;
  const routeTo = document.getElementById('route-to').value;

  if (!company || isNaN(passengers) || isNaN(pricePerHour) || isNaN(hours) || !datetimeStr || (isNewCustomer && !newCompanyName)) {
    alert('Пожалуйста, заполните все поля корректно перед выбором ТС.');
    return;
  }

  // Формирование даты
  const [datePart, timePart] = datetimeStr.split(' ');
  const [yyyy, mm, dd] = datePart.split('-').map(Number);
  const [hh, min, ss] = timePart.split(':').map(Number);
  const start = new Date(yyyy, mm - 1, dd, hh, min, ss);
  const end = new Date(start.getTime() + hours * 60 * 60 * 1000);

  const pad = n => n.toString().padStart(2, '0');
  const format = dt => `${dt.getFullYear()}-${pad(dt.getMonth() + 1)}-${pad(dt.getDate())} ${pad(dt.getHours())}:${pad(dt.getMinutes())}:${pad(dt.getSeconds())}`;
  const formattedStart = format(start);
  const formattedEnd = format(end);
  const totalCost = Math.round(pricePerHour * hours);

  const postData = {
    company,
    passengers,
    price: pricePerHour,
    status,
    new_company_name: isNewCustomer ? newCompanyName : '',
    booking_start: formattedStart,
    booking_end: formattedEnd,
    duration_hours: hours,
    total_price: totalCost,
    vehicle_type: selectedTransportType,
    route_from: routeFrom,
    route_to: routeTo,
    wants_preferred_type: preferredAlt,
    contact: document.getElementById(`notify-contact-${preferredAlt?.replace(/\s+/g, '-')}`)?.value || ""
  };

  fetch('https://bbus-project.onrender.com/api/save_order', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(postData)
  })
    .then(response => {
      if (!response.ok) {
        return response.json().then(err => { throw new Error(err.error); });
      }
      return response.json();
    })
    .then(() => {
      alert('Заказ успешно сохранен');
    })
    .catch(err => {
      alert(`Ошибка: ${err.message}`);
    });
}

function saveWithoutTransport(type, contactInputId) {
  const contact = document.getElementById(contactInputId).value;

  const company = input.value;
  const passengers = parseInt(document.getElementById('passengers').value);
  const pricePerHour = parseFloat(document.getElementById('price').value);
  const hours = parseFloat(document.getElementById('hours').value);
  const status = document.getElementById('status').value;
  const newCompanyName = newCompanyInput.value;
  const datetimeStr = document.getElementById("booking_datetime").value;
  const routeFrom = document.getElementById('route-from').value;
  const routeTo = document.getElementById('route-to').value;

  if (!company || isNaN(passengers) || isNaN(pricePerHour) || isNaN(hours) || !datetimeStr || (isNewCustomer && !newCompanyName)) {
    alert('Пожалуйста, заполните все поля корректно.');
    return;
  }

  const [datePart, timePart] = datetimeStr.split(' ');
  const [yyyy, mm, dd] = datePart.split('-').map(Number);
  const [hh, min, ss] = timePart.split(':').map(Number);
  const start = new Date(yyyy, mm - 1, dd, hh, min, ss);
  const end = new Date(start.getTime() + hours * 60 * 60 * 1000);

  const pad = n => n.toString().padStart(2, '0');
  const format = dt => `${dt.getFullYear()}-${pad(dt.getMonth() + 1)}-${pad(dt.getDate())} ${pad(dt.getHours())}:${pad(dt.getMinutes())}:${pad(dt.getSeconds())}`;
  const formattedStart = format(start);
  const formattedEnd = format(end);
  const totalCost = Math.round(pricePerHour * hours);

  const postData = {
    company,
    passengers,
    price: pricePerHour,
    status,
    new_company_name: isNewCustomer ? newCompanyName : '',
    booking_start: formattedStart,
    booking_end: formattedEnd,
    duration_hours: hours,
    total_price: totalCost,
    vehicle_type: '',
    route_from: routeFrom,
    route_to: routeTo,
    wants_preferred_type: type,
    contact
  };

  fetch('https://bbus-project.onrender.com/api/save_order', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(postData)
  })
    .then(response => {
      if (!response.ok) {
        return response.json().then(err => { throw new Error(err.error); });
      }
      return response.json();
    })
    .then(() => {
      alert('Заказ сохранен без выбора ТС');
    })
    .catch(err => {
      alert(`Ошибка: ${err.message}`);
    });
}

function calculateAndStoreBookingTimes() {
  const datetimeStr = datetimeInput.value;
  const hours = parseFloat(document.getElementById("hours").value);
  if (!datetimeStr || isNaN(hours)) return;

  const [datePart, timePart] = datetimeStr.split(' ');
  const [yyyy, mm, dd] = datePart.split('-').map(Number);
  const [hh, min, ss] = timePart.split(':').map(Number);
  const start = new Date(yyyy, mm - 1, dd, hh, min, ss);
  const end = new Date(start.getTime() + hours * 60 * 60 * 1000);

  const pad = n => n.toString().padStart(2, '0');
  const format = dt => `${dt.getFullYear()}-${pad(dt.getMonth() + 1)}-${pad(dt.getDate())} ${pad(dt.getHours())}:${pad(dt.getMinutes())}:${pad(dt.getSeconds())}`;
  const formattedStart = format(start);
  const formattedEnd = format(end);

  localStorage.setItem("lastBookingStart", formattedStart);
  localStorage.setItem("lastBookingEnd", formattedEnd);
}

const datetimeInput = document.getElementById("booking_datetime");

datetimeInput.addEventListener("blur", () => {
  const value = datetimeInput.value.trim();
  if (!value.match(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/)) {
    // alert("Неверный формат. Используйте: ГГГГ-ММ-ДД ЧЧ:ММ:СС");
    // datetimeInput.focus();
  }
});

datetimeInput.addEventListener("input", calculateAndStoreBookingTimes);
document.getElementById("hours").addEventListener("input", calculateAndStoreBookingTimes);
