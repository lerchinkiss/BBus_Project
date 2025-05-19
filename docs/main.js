let knownCompanies = [];
let isNewCustomer = false;

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
  warning.style.display = (input.value < 1 || input.value > 59) ? 'block' : 'none';
}

document.getElementById('submit-button').onclick = function (e) {
  e.preventDefault();

  const company = input.value;
  const passengers = document.getElementById('passengers').value;
  const pricePerHour = parseFloat(document.getElementById('price').value);
  const hours = parseFloat(document.getElementById('hours').value);
  const status = document.getElementById('status').value;
  const newCompanyName = newCompanyInput.value;
  const datetimeStr = document.getElementById("booking_datetime").value;

  if (!company || isNaN(passengers) || isNaN(pricePerHour) || isNaN(hours) || !datetimeStr || (isNewCustomer && !newCompanyName)) {
    alert('Пожалуйста, заполните все поля формы корректно');
    return;
  }

  // Расчёт времени бронирования
  const start = new Date(datetimeStr);
  const end = new Date(start.getTime() + hours * 60 * 60 * 1000);

  const pad = n => n.toString().padStart(2, '0');
  const format = dt => `${dt.getFullYear()}-${pad(dt.getMonth() + 1)}-${pad(dt.getDate())} ${pad(dt.getHours())}:${pad(dt.getMinutes())}`;
  const formattedStart = format(start);
  const formattedEnd = format(end);

  const totalCost = Math.round(pricePerHour * hours);
  document.getElementById("price-summary").textContent = `К оплате: ${totalCost.toLocaleString('ru-RU')} руб.`;

  const postData = {
    company,
    passengers,
    price: pricePerHour,
    status,
    new_company_name: isNewCustomer ? newCompanyName : '',
    booking_start: formattedStart,
    booking_end: formattedEnd,
    duration_hours: hours
  };

  // Получение рекомендаций и сохранение заказа
  fetch('https://bbus-project.onrender.com/api/recommend', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(postData)
  })
    .then(response => response.json())
    .then(recommendations => {
      const box = document.querySelector('.recommendations-box');
      let html = '<div class="section-title">Рекомендованные типы ТС</div>';
      if (!recommendations.length) {
        html += '<p>Не удалось найти подходящий транспорт по количеству пассажиров.</p>';
      } else {
        recommendations.forEach(rec => {
          html += `
            <div class="recommendation">
              <p><strong>${rec.type}</strong> (вместимость: ${rec.capacity} мест)</p>
              <p>Вероятность: ${(rec.probability * 100).toFixed(1)}%</p>
            </div>`;
        });
      }
      box.innerHTML = html;

      // Сохраняем заказ
      fetch('https://bbus-project.onrender.com/api/save_order', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...postData, recommendations })
      });
    });
};


function calculateAndStoreBookingTimes() {
  const datetimeStr = document.getElementById("booking_datetime").value;
  const hours = parseFloat(document.getElementById("hours").value);

  if (!datetimeStr || isNaN(hours)) return;

  const start = new Date(datetimeStr);
  const end = new Date(start.getTime() + hours * 60 * 60 * 1000);

  const pad = n => n.toString().padStart(2, '0');
  const format = dt => `${dt.getFullYear()}-${pad(dt.getMonth() + 1)}-${pad(dt.getDate())} ${pad(dt.getHours())}:${pad(dt.getMinutes())}`;

  const formattedStart = format(start);
  const formattedEnd = format(end);

  // Сохраняем во временное хранилище
  localStorage.setItem("lastBookingStart", formattedStart);
  localStorage.setItem("lastBookingEnd", formattedEnd);
}

// Вызовем при любом изменении даты или часов
document.getElementById("booking_datetime").addEventListener("input", calculateAndStoreBookingTimes);
document.getElementById("hours").addEventListener("input", calculateAndStoreBookingTimes);

