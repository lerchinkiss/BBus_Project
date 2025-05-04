// === main.js ===

let knownCompanies = [];

fetch('https://bbus-project.onrender.com/api/companies')
  .then(response => response.json())
  .then(companies => {
    knownCompanies = companies;
  });

const input = document.getElementById('company-input');
const suggestions = document.getElementById('company-suggestions');

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
  const maxSuggestions = 10;
  const value = input.value.toLowerCase();
  
  // Если введено значение, которое не соответствует ни одной компании
  if (value && !knownCompanies.some(name => name.toLowerCase() === value)) {
    const div = document.createElement('div');
    div.textContent = 'Новый заказчик';
    div.style.fontWeight = 'bold';
    div.style.color = '#800000';
    div.onclick = () => selectCompany('Новый заказчик');
    suggestions.appendChild(div);
  }
  
  // Показываем только первые 10 компаний
  companies.slice(0, maxSuggestions).forEach(company => {
    const div = document.createElement('div');
    div.textContent = company;
    div.onclick = () => selectCompany(company);
    suggestions.appendChild(div);
  });
  
  suggestions.style.display = 'block';
}

function selectCompany(name) {
  if (name === "Новый заказчик") {
    input.value = "Новый заказчик";
    document.getElementById('new-company-container').style.display = 'block';
    document.getElementById('new-company').focus();
  } else {
    input.value = name;
    document.getElementById('new-company-container').style.display = 'none';
  }
  suggestions.style.display = 'none';

  const preferencesBox = document.querySelector('.preferences-box');
  const recommendationsBox = document.querySelector('.recommendations-box');
  const historyTable = document.querySelector('.table-box tbody');

  if (name === 'Новый заказчик') {
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

  fetch(`https://bbus-project.onrender.com/api/recommendations/${encodeURIComponent(name)}`)
    .then(response => response.json())
    .then(data => {
      if (data.error) {
        recommendationsBox.innerHTML = '<div class="section-title">Рекомендованные типы ТС</div><p>Нет данных</p>';
      } else {
        recommendationsBox.innerHTML = `
          <div class="section-title">Рекомендованные типы ТС</div>
          <p><strong>Рекомендуемый тип ТС:</strong> ${data.рекомендуемый_тип_тс}</p>
          <p><strong>Вероятность выбора:</strong> ${(data.вероятность * 100).toFixed(1)}%</p>
          <p><strong>Альтернативные варианты:</strong> ${data.альтернативы.join(', ')}</p>
        `;
      }
    });

  // Получаем текстовые описания маршрутов
  fetch(`https://bbus-project.onrender.com/api/route_texts/${encodeURIComponent(name)}`)
    .then(response => response.json())
    .then(data => {
      const routeTexts = data.route_texts;
      const select = document.getElementById('route');
      
      select.innerHTML = '';
      routeTexts.forEach(route => {
        const option = document.createElement('option');
        option.value = route.id;
        option.textContent = route.text;
        select.appendChild(option);
      });
    })
    .catch(error => {
      console.error('Ошибка при получении текстовых описаний маршрутов:', error);
    });
}

function validatePassengers(input) {
  const warning = document.getElementById('passenger-warning');
  warning.style.display = (input.value < 1 || input.value > 59) ? 'block' : 'none';
}

document.getElementById('submit-button').onclick = function(e) {
  e.preventDefault();
  const company = document.getElementById('company-input').value;
  const passengers = document.getElementById('passengers').value;
  const price = document.getElementById('price').value;
  const status = document.getElementById('status').value;

  if (!company || !passengers || !price) {
    alert('Пожалуйста, заполните все поля формы');
    return;
  }

  // Сначала сохраняем заказ
  const orderData = {
    company: company,
    passengers: parseInt(passengers),
    price: parseFloat(price),
    status: status,
    date: new Date().toISOString().split('T')[0]
  };

  fetch('https://bbus-project.onrender.com/api/save_order', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(orderData)
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      // После успешного сохранения экспортируем в Excel
      fetch(`https://bbus-project.onrender.com/api/export_excel/${encodeURIComponent(company)}`)
        .then(response => response.blob())
        .then(blob => {
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `${company}_orders.xlsx`;
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          document.body.removeChild(a);
        })
        .catch(error => {
          console.error('Ошибка при экспорте данных:', error);
        });

      // Обновляем историю заказов
      selectCompany(company);
      // Очищаем форму
      document.getElementById('passengers').value = '';
      document.getElementById('price').value = '';
      document.getElementById('status').value = 'Стандарт';
    } else {
      alert('Ошибка при сохранении заказа: ' + data.error);
    }
  })
  .catch(error => {
    alert('Ошибка при сохранении заказа: ' + error);
  });
};

// Получаем список компаний при загрузке страницы
fetch('https://bbus-project.onrender.com/api/companies')
    .then(response => response.json())
    .then(data => {
        const companies = data.companies;
        const input = document.getElementById('company-input');
        const suggestions = document.getElementById('company-suggestions');

        input.addEventListener('input', function() {
            const value = this.value.toLowerCase();
            const filtered = companies.filter(company => 
                company.toLowerCase().includes(value)
            ).slice(0, 5); // Показываем только первые 5 результатов

            suggestions.innerHTML = '';
            if (value.length > 0) {
                filtered.forEach(company => {
                    const div = document.createElement('div');
                    div.textContent = company;
                    div.addEventListener('click', () => selectCompany(company));
                    suggestions.appendChild(div);
                });
                suggestions.style.display = 'block';
            } else {
                suggestions.style.display = 'none';
            }
        });

        // Добавляем "Новый заказчик" в список
        const newCustomer = document.createElement('div');
        newCustomer.textContent = 'Новый заказчик';
        newCustomer.addEventListener('click', () => selectCompany('Новый заказчик'));
        suggestions.appendChild(newCustomer);
    })
    .catch(error => {
        console.error('Ошибка при получении списка компаний:', error);
    });

// Получаем список типов ТС при загрузке страницы
fetch('https://bbus-project.onrender.com/api/vehicle_types')
    .then(response => response.json())
    .then(data => {
        const vehicleTypes = data.vehicle_types;
        const select = document.getElementById('vehicle-type');
        
        vehicleTypes.forEach(type => {
            const option = document.createElement('option');
            option.value = type;
            option.textContent = type;
            select.appendChild(option);
        });
    })
    .catch(error => {
        console.error('Ошибка при получении списка типов ТС:', error);
    });

// Получаем список статусов при загрузке страницы
fetch('https://bbus-project.onrender.com/api/statuses')
    .then(response => response.json())
    .then(data => {
        const statuses = data.statuses;
        const select = document.getElementById('status');
        
        statuses.forEach(status => {
            const option = document.createElement('option');
            option.value = status;
            option.textContent = status;
            select.appendChild(option);
        });
    })
    .catch(error => {
        console.error('Ошибка при получении списка статусов:', error);
    });

// Получаем список типов заказов при загрузке страницы
fetch('https://bbus-project.onrender.com/api/order_types')
    .then(response => response.json())
    .then(data => {
        const orderTypes = data.order_types;
        const select = document.getElementById('type');
        
        orderTypes.forEach(type => {
            const option = document.createElement('option');
            option.value = type;
            option.textContent = type;
            select.appendChild(option);
        });
    })
    .catch(error => {
        console.error('Ошибка при получении списка типов заказов:', error);
    });

// Получаем список маршрутов при загрузке страницы
fetch('https://bbus-project.onrender.com/api/routes')
    .then(response => response.json())
    .then(data => {
        const routes = data.routes;
        const select = document.getElementById('route');
        
        routes.forEach(route => {
            const option = document.createElement('option');
            option.value = route;
            option.textContent = route;
            select.appendChild(option);
        });
    })
    .catch(error => {
        console.error('Ошибка при получении списка маршрутов:', error);
    });

// Получаем список пассажиров при загрузке страницы
fetch('https://bbus-project.onrender.com/api/passengers')
    .then(response => response.json())
    .then(data => {
        const passengers = data.passengers;
        const select = document.getElementById('passengers');
        
        passengers.forEach(passenger => {
            const option = document.createElement('option');
            option.value = passenger;
            option.textContent = passenger;
            select.appendChild(option);
        });
    })
    .catch(error => {
        console.error('Ошибка при получении списка пассажиров:', error);
    });

// Получаем список цен при загрузке страницы
fetch('https://bbus-project.onrender.com/api/prices')
    .then(response => response.json())
    .then(data => {
        const prices = data.prices;
        const select = document.getElementById('price');
        
        prices.forEach(price => {
            const option = document.createElement('option');
            option.value = price;
            option.textContent = price;
            select.appendChild(option);
        });
    })
    .catch(error => {
        console.error('Ошибка при получении списка цен:', error);
    });

// Получаем список дат при загрузке страницы
fetch('https://bbus-project.onrender.com/api/dates')
    .then(response => response.json())
    .then(data => {
        const dates = data.dates;
        const select = document.getElementById('date');
        
        dates.forEach(date => {
            const option = document.createElement('option');
            option.value = date;
            option.textContent = date;
            select.appendChild(option);
        });
    })
    .catch(error => {
        console.error('Ошибка при получении списка дат:', error);
    });

// Получаем список типов ТС для рекомендаций при загрузке страницы
fetch('https://bbus-project.onrender.com/api/recommendation_types')
    .then(response => response.json())
    .then(data => {
        const types = data.types;
        const select = document.getElementById('recommendation-type');
        
        types.forEach(type => {
            const option = document.createElement('option');
            option.value = type;
            option.textContent = type;
            select.appendChild(option);
        });
    })
    .catch(error => {
        console.error('Ошибка при получении списка типов ТС для рекомендаций:', error);
    });

// Получаем список альтернативных вариантов при загрузке страницы
fetch('https://bbus-project.onrender.com/api/alternatives')
    .then(response => response.json())
    .then(data => {
        const alternatives = data.alternatives;
        const select = document.getElementById('alternatives');
        
        alternatives.forEach(alternative => {
            const option = document.createElement('option');
            option.value = alternative;
            option.textContent = alternative;
            select.appendChild(option);
        });
    })
    .catch(error => {
        console.error('Ошибка при получении списка альтернативных вариантов:', error);
    });

// Получаем список вероятностей при загрузке страницы
fetch('https://bbus-project.onrender.com/api/probabilities')
    .then(response => response.json())
    .then(data => {
        const probabilities = data.probabilities;
        const select = document.getElementById('probability');
        
        probabilities.forEach(probability => {
            const option = document.createElement('option');
            option.value = probability;
            option.textContent = probability;
            select.appendChild(option);
        });
    })
    .catch(error => {
        console.error('Ошибка при получении списка вероятностей:', error);
    });

// Получаем список моделей ТС при загрузке страницы
fetch('https://bbus-project.onrender.com/api/models')
    .then(response => response.json())
    .then(data => {
        const models = data.models;
        const select = document.getElementById('model');
        
        models.forEach(model => {
            const option = document.createElement('option');
            option.value = model;
            option.textContent = model;
            select.appendChild(option);
        });
    })
    .catch(error => {
        console.error('Ошибка при получении списка моделей ТС:', error);
    });

// Получаем список статусов заказов при загрузке страницы
fetch('https://bbus-project.onrender.com/api/order_statuses')
    .then(response => response.json())
    .then(data => {
        const statuses = data.statuses;
        const select = document.getElementById('order-status');
        
        statuses.forEach(status => {
            const option = document.createElement('option');
            option.value = status;
            option.textContent = status;
            select.appendChild(option);
        });
    })
    .catch(error => {
        console.error('Ошибка при получении списка статусов заказов:', error);
    });

// Получаем список средних пассажиров при загрузке страницы
fetch('https://bbus-project.onrender.com/api/average_passengers')
    .then(response => response.json())
    .then(data => {
        const passengers = data.passengers;
        const select = document.getElementById('average-passengers');
        
        passengers.forEach(passenger => {
            const option = document.createElement('option');
            option.value = passenger;
            option.textContent = passenger;
            select.appendChild(option);
        });
    })
    .catch(error => {
        console.error('Ошибка при получении списка средних пассажиров:', error);
    });

// Получаем список всего заказов при загрузке страницы
fetch('https://bbus-project.onrender.com/api/total_orders')
    .then(response => response.json())
    .then(data => {
        const orders = data.orders;
        const select = document.getElementById('total-orders');
        
        orders.forEach(order => {
            const option = document.createElement('option');
            option.value = order;
            option.textContent = order;
            select.appendChild(option);
        });
    })
    .catch(error => {
        console.error('Ошибка при получении списка всего заказов:', error);
    });

// Получаем список маршрутов для истории при загрузке страницы
fetch('https://bbus-project.onrender.com/api/history_routes')
    .then(response => response.json())
    .then(data => {
        const routes = data.routes;
        const select = document.getElementById('history-route');
        
        routes.forEach(route => {
            const option = document.createElement('option');
            option.value = route;
            option.textContent = route;
            select.appendChild(option);
        });
    })
    .catch(error => {
        console.error('Ошибка при получении списка маршрутов для истории:', error);
    });

// Получаем список дат для истории при загрузке страницы
fetch('https://bbus-project.onrender.com/api/history_dates')
    .then(response => response.json())
    .then(data => {
        const dates = data.dates;
        const select = document.getElementById('history-date');
        
        dates.forEach(date => {
            const option = document.createElement('option');
            option.value = date;
            option.textContent = date;
            select.appendChild(option);
        });
    })
    .catch(error => {
        console.error('Ошибка при получении списка дат для истории:', error);
    });

// Получаем список типов ТС для истории при загрузке страницы
fetch('https://bbus-project.onrender.com/api/history_types')
    .then(response => response.json())
    .then(data => {
        const types = data.types;
        const select = document.getElementById('history-type');
        
        types.forEach(type => {
            const option = document.createElement('option');
            option.value = type;
            option.textContent = type;
            select.appendChild(option);
        });
    })
    .catch(error => {
        console.error('Ошибка при получении списка типов ТС для истории:', error);
    });

// Получаем список пассажиров для истории при загрузке страницы
fetch('https://bbus-project.onrender.com/api/history_passengers')
    .then(response => response.json())
    .then(data => {
        const passengers = data.passengers;
        const select = document.getElementById('history-passengers');
        
        passengers.forEach(passenger => {
            const option = document.createElement('option');
            option.value = passenger;
            option.textContent = passenger;
            select.appendChild(option);
        });
    })
    .catch(error => {
        console.error('Ошибка при получении списка пассажиров для истории:', error);
    });

// Получаем список цен для истории при загрузке страницы
fetch('https://bbus-project.onrender.com/api/history_prices')
    .then(response => response.json())
    .then(data => {
        const prices = data.prices;
        const select = document.getElementById('history-price');
        
        prices.forEach(price => {
            const option = document.createElement('option');
            option.value = price;
            option.textContent = price;
            select.appendChild(option);
        });
    })
    .catch(error => {
        console.error('Ошибка при получении списка цен для истории:', error);
    });

// Получаем список типов заказов для истории при загрузке страницы
fetch('https://bbus-project.onrender.com/api/history_order_types')
    .then(response => response.json())
    .then(data => {
        const types = data.types;
        const select = document.getElementById('history-order-type');
        
        types.forEach(type => {
            const option = document.createElement('option');
            option.value = type;
            option.textContent = type;
            select.appendChild(option);
        });
    })
    .catch(error => {
        console.error('Ошибка при получении списка типов заказов для истории:', error);
    });

// Получаем список статусов заказов для истории при загрузке страницы
fetch('https://bbus-project.onrender.com/api/history_order_statuses')
    .then(response => response.json())
    .then(data => {
        const statuses = data.statuses;
        const select = document.getElementById('history-order-status');
        
        statuses.forEach(status => {
            const option = document.createElement('option');
            option.value = status;
            option.textContent = status;
            select.appendChild(option);
        });
    })
    .catch(error => {
        console.error('Ошибка при получении списка статусов заказов для истории:', error);
    });

// Получаем список маршрутов для отображения в виде текста
fetch('https://bbus-project.onrender.com/api/route_texts')
    .then(response => response.json())
    .then(data => {
        const routeTexts = data.route_texts;
        const select = document.getElementById('route');
        
        routeTexts.forEach(route => {
            const option = document.createElement('option');
            option.value = route.id;
            option.textContent = route.text;
            select.appendChild(option);
        });
    })
    .catch(error => {
        console.error('Ошибка при получении списка маршрутов для отображения:', error);
    });

// Получаем список маршрутов для истории для отображения в виде текста
fetch('https://bbus-project.onrender.com/api/history_route_texts')
    .then(response => response.json())
    .then(data => {
        const routeTexts = data.route_texts;
        const select = document.getElementById('history-route');
        
        select.innerHTML = '';
        routeTexts.forEach(route => {
            const option = document.createElement('option');
            option.value = route.id;
            option.textContent = route.text;
            select.appendChild(option);
        });
    })
    .catch(error => {
        console.error('Ошибка при получении текстовых описаний маршрутов для истории:', error);
    });

function getRecommendations() {
    const company = document.getElementById('company').value;
    const passengers = parseInt(document.getElementById('passengers').value);
    const route = document.getElementById('route').value;
    const price = parseFloat(document.getElementById('price').value);
    const type = document.getElementById('type').value;
    const status = document.getElementById('status').value;
    const vehicleType = document.getElementById('vehicle-type').value;

    if (!company || !passengers || !route || !price || !type || !status || !vehicleType) {
        alert('Пожалуйста, заполните все поля');
        return;
    }

    const data = {
        company,
        passengers,
        route,
        price,
        type,
        status,
        vehicle_type: vehicleType
    };

    fetch('https://bbus-project.onrender.com/api/recommendations', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        const recommendationsBox = document.querySelector('.recommendations-box');
        recommendationsBox.innerHTML = `
            <div class="section-title">Рекомендованные типы ТС</div>
            <p><strong>Рекомендуемый тип ТС:</strong> ${data.рекомендуемый_тип_тс}</p>
            <p><strong>Вероятность выбора:</strong> ${(data.вероятность * 100).toFixed(1)}%</p>
            <p><strong>Альтернативные варианты:</strong> ${data.альтернативы.join(', ')}</p>
        `;

        // Сохраняем заказ и экспортируем в Excel
        const orderData = {
            company,
            passengers,
            price,
            status,
            date: new Date().toISOString().split('T')[0]
        };

        fetch('https://bbus-project.onrender.com/api/save_order', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(orderData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Экспортируем в Excel
                fetch(`https://bbus-project.onrender.com/api/export_excel/${encodeURIComponent(company)}`)
                    .then(response => response.blob())
                    .then(blob => {
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `заказы_${company}.xlsx`;
                        document.body.appendChild(a);
                        a.click();
                        window.URL.revokeObjectURL(url);
                        document.body.removeChild(a);
                    })
                    .catch(error => {
                        console.error('Ошибка при экспорте в Excel:', error);
                    });
            }
        })
        .catch(error => {
            console.error('Ошибка при сохранении заказа:', error);
        });
    })
    .catch(error => {
        console.error('Ошибка при получении рекомендаций:', error);
        alert('Произошла ошибка при получении рекомендаций');
    });
}

function getHistory() {
    const company = document.getElementById('company').value;
    const passengers = document.getElementById('history-passengers').value;
    const price = document.getElementById('history-price').value;
    const orderType = document.getElementById('history-order-type').value;
    const orderStatus = document.getElementById('history-order-status').value;
    const route = document.getElementById('history-route').value;
    const date = document.getElementById('history-date').value;
    const vehicleType = document.getElementById('history-vehicle-type').value;

    const data = {
        company,
        passengers,
        price,
        order_type: orderType,
        order_status: orderStatus,
        route,
        date,
        vehicle_type: vehicleType
    };

    fetch('https://bbus-project.onrender.com/api/history', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        const historyTable = document.querySelector('.table-box tbody');
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
    })
    .catch(error => {
        console.error('Ошибка при получении истории:', error);
        alert('Произошла ошибка при получении истории');
    });
}

function getRouteTexts() {
    const company = document.getElementById('company').value;
    fetch(`https://bbus-project.onrender.com/api/route_texts/${encodeURIComponent(company)}`)
        .then(response => response.json())
        .then(data => {
            const routeTexts = data.route_texts;
            const select = document.getElementById('route');
            
            select.innerHTML = '';
            routeTexts.forEach(route => {
                const option = document.createElement('option');
                option.value = route.id;
                option.textContent = route.text;
                select.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Ошибка при получении текстовых описаний маршрутов:', error);
        });
}

function getHistoryRoutes() {
    const company = document.getElementById('company').value;
    fetch(`https://bbus-project.onrender.com/api/history_routes/${encodeURIComponent(company)}`)
        .then(response => response.json())
        .then(data => {
            const routes = data.routes;
            const select = document.getElementById('history-route');
            
            select.innerHTML = '';
            routes.forEach(route => {
                const option = document.createElement('option');
                option.value = route.id;
                option.textContent = route.text;
                select.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Ошибка при получении списка маршрутов для истории:', error);
        });
}

function getRoutes() {
    const company = document.getElementById('company').value;
    fetch(`https://bbus-project.onrender.com/api/routes/${encodeURIComponent(company)}`)
        .then(response => response.json())
        .then(data => {
            const routes = data.routes;
            const select = document.getElementById('route');
            
            select.innerHTML = '';
            routes.forEach(route => {
                const option = document.createElement('option');
                option.value = route.id;
                option.textContent = route.text;
                select.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Ошибка при получении списка маршрутов:', error);
        });
}

function getHistoryRouteTextsForDisplay() {
    const company = document.getElementById('company').value;
    fetch(`https://bbus-project.onrender.com/api/history_route_texts_for_display/${encodeURIComponent(company)}`)
        .then(response => response.json())
        .then(data => {
            const routeTexts = data.route_texts;
            const select = document.getElementById('history-route');
            
            select.innerHTML = '';
            routeTexts.forEach(route => {
                const option = document.createElement('option');
                option.value = route.id;
                option.textContent = route.text;
                select.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Ошибка при получении текстовых описаний маршрутов для истории для отображения:', error);
        });
}

function getHistoryRoutesForDisplay() {
    const company = document.getElementById('company').value;
    fetch(`https://bbus-project.onrender.com/api/history_routes_for_display/${encodeURIComponent(company)}`)
        .then(response => response.json())
        .then(data => {
            const routes = data.routes;
            const select = document.getElementById('history-route');
            
            select.innerHTML = '';
            routes.forEach(route => {
                const option = document.createElement('option');
                option.value = route.id;
                option.textContent = route.text;
                select.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Ошибка при получении списка маршрутов для истории для отображения:', error);
        });
}

function getRoutesForDisplay() {
    const company = document.getElementById('company').value;
    fetch(`https://bbus-project.onrender.com/api/routes_for_display/${encodeURIComponent(company)}`)
        .then(response => response.json())
        .then(data => {
            const routes = data.routes;
            const select = document.getElementById('route');
            
            select.innerHTML = '';
            routes.forEach(route => {
                const option = document.createElement('option');
                option.value = route.id;
                option.textContent = route.text;
                select.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Ошибка при получении списка маршрутов для отображения:', error);
        });
}

function getRoutesForDisplayForHistory() {
    const company = document.getElementById('company').value;
    fetch(`https://bbus-project.onrender.com/api/routes_for_display_for_history/${encodeURIComponent(company)}`)
        .then(response => response.json())
        .then(data => {
            const routes = data.routes;
            const select = document.getElementById('route');
            
            select.innerHTML = '';
            routes.forEach(route => {
                const option = document.createElement('option');
                option.value = route.id;
                option.textContent = route.text;
                select.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Ошибка при получении списка маршрутов для отображения для истории:', error);
        });
}

function getRouteTextsForDisplayForHistory() {
    const company = document.getElementById('company').value;
    fetch(`https://bbus-project.onrender.com/api/route_texts_for_display_for_history/${encodeURIComponent(company)}`)
        .then(response => response.json())
        .then(data => {
            const routeTexts = data.route_texts;
            const select = document.getElementById('route');
            
            select.innerHTML = '';
            routeTexts.forEach(route => {
                const option = document.createElement('option');
                option.value = route.id;
                option.textContent = route.text;
                select.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Ошибка при получении текстовых описаний маршрутов для отображения для истории:', error);
        });
}

function getHistoryRouteTextsForDisplayForHistoryForHistoryForHistoryForHistoryForHistoryForHistoryForHistoryForHistory() {
    const company = document.getElementById('company').value;
    fetch(`https://bbus-project.onrender.com/api/history_route_texts_for_display_for_history_for_history_for_history_for_history_for_history_for_history_for_history_for_history/${encodeURIComponent(company)}`)
        .then(response => response.json())
        .then(data => {
            const routeTexts = data.route_texts;
            const select = document.getElementById('history-route');
            
            select.innerHTML = '';
            routeTexts.forEach(route => {
                const option = document.createElement('option');
                option.value = route.id;
                option.textContent = route.text;
                select.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Ошибка при получении текстовых описаний маршрутов для истории для отображения для истории для истории для истории для истории для истории для истории для истории для истории для истории:', error);
        });
}

function getRouteTextsForDisplayForHistoryForHistoryForHistoryForHistoryForHistoryForHistoryForHistory() {
    const company = document.getElementById('company').value;
    fetch(`https://bbus-project.onrender.com/api/route_texts_for_display_for_history_for_history_for_history_for_history_for_history_for_history_for_history_for_history_for_history_for_history/${encodeURIComponent(company)}`)
        .then(response => response.json())
        .then(data => {
            const routeTexts = data.route_texts;
            const select = document.getElementById('route');
            
            select.innerHTML = '';
            routeTexts.forEach(route => {
                const option = document.createElement('option');
                option.value = route.id;
                option.textContent = route.text;
                select.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Ошибка при получении текстовых описаний маршрутов для отображения для истории для истории для истории для истории для истории для истории для истории для истории для истории для истории:', error);
        });
}

function getHistoryRoutesForDisplayForHistoryForHistoryForHistoryForHistoryForHistoryForHistory() {
    const company = document.getElementById('company').value;
    fetch(`https://bbus-project.onrender.com/api/history_routes_for_display_for_history_for_history_for_history_for_history_for_history_for_history_for_history_for_history_for_history_for_history/${encodeURIComponent(company)}`)
        .then(response => response.json())
        .then(data => {
            const routes = data.routes;
            const select = document.getElementById('history-route');
            
            select.innerHTML = '';
            routes.forEach(route => {
                const option = document.createElement('option');
                option.value = route.id;
                option.textContent = route.text;
                select.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Ошибка при получении списка маршрутов для истории для отображения для истории для истории для истории для истории для истории для истории для истории для истории для истории:', error);
        });
}

function getRoutesForDisplayForHistoryForHistory() {
    const company = document.getElementById('company').value;
    fetch(`https://bbus-project.onrender.com/api/routes_for_display_for_history_for_history_for_history_for_history_for_history_for_history_for_history/${encodeURIComponent(company)}`)
        .then(response => response.json())
        .then(data => {
            const routes = data.routes;
            const select = document.getElementById('route');
            
            select.innerHTML = '';
            routes.forEach(route => {
                const option = document.createElement('option');
                option.value = route.id;
                option.textContent = route.text;
                select.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Ошибка при получении списка маршрутов для отображения для истории для истории для истории для истории для истории для истории:', error);
        });
}

function getHistoryRoutesForDisplayForHistoryForHistoryForHistory() {
    const company = document.getElementById('company').value;
    fetch(`https://bbus-project.onrender.com/api/history_routes_for_display_for_history_for_history_for_history_for_history_for_history_for_history_for_history_for_history_for_history/${encodeURIComponent(company)}`)
        .then(response => response.json())
        .then(data => {
            const routes = data.routes;
            const select = document.getElementById('history-route');
            
            select.innerHTML = '';
            routes.forEach(route => {
                const option = document.createElement('option');
                option.value = route.id;
                option.textContent = route.text;
                select.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Ошибка при получении списка маршрутов для истории для отображения для истории для истории для истории для истории для истории для истории для истории:', error);
        });
}

function getRoutesForDisplayForHistoryForHistoryForHistoryForHistoryForHistoryForHistory() {
    const company = document.getElementById('company').value;
    fetch(`https://bbus-project.onrender.com/api/routes_for_display_for_history_for_history_for_history_for_history_for_history_for_history_for_history_for_history_for_history/${encodeURIComponent(company)}`)
        .then(response => response.json())
        .then(data => {
            const routes = data.routes;
            const select = document.getElementById('route');
            
            select.innerHTML = '';
            routes.forEach(route => {
                const option = document.createElement('option');
                option.value = route.id;
                option.textContent = route.text;
                select.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Ошибка при получении списка маршрутов для отображения для истории для истории для истории для истории для истории для истории для истории:', error);
        });
}

function getHistoryRouteTextsForDisplayForHistoryForHistoryForHistoryForHistoryForHistoryForHistory() {
    const company = document.getElementById('company').value;
    fetch(`https://bbus-project.onrender.com/api/history_route_texts_for_display_for_history_for_history_for_history_for_history_for_history_for_history_for_history_for_history_for_history/${encodeURIComponent(company)}`)
        .then(response => response.json())
        .then(data => {
            const routeTexts = data.route_texts;
            const select = document.getElementById('history-route');
            
            select.innerHTML = '';
            routeTexts.forEach(route => {
                const option = document.createElement('option');
                option.value = route.id;
                option.textContent = route.text;
                select.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Ошибка при получении текстовых описаний маршрутов для отображения для истории для истории для истории для истории для истории для истории для истории для истории:', error);
        });
}

function getRouteTextsForDisplayForHistoryForHistoryForHistoryForHistoryForHistoryForHistoryForHistory() {
    const company = document.getElementById('company').value;
    fetch(`https://bbus-project.onrender.com/api/route_texts_for_display_for_history_for_history_for_history_for_history_for_history_for_history_for_history_for_history_for_history_for_history/${encodeURIComponent(company)}`)
        .then(response => response.json())
        .then(data => {
            const routeTexts = data.route_texts;
            const select = document.getElementById('route');
            
            select.innerHTML = '';
            routeTexts.forEach(route => {
                const option = document.createElement('option');
                option.value = route.id;
                option.textContent = route.text;
                select.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Ошибка при получении текстовых описаний маршрутов для отображения для истории для истории для истории для истории для истории для истории для истории для истории:', error);
        });
}

function getRoutesForDisplayForHistoryForHistoryForHistoryForHistoryForHistoryForHistory() {
    const company = document.getElementById('company').value;
    fetch(`https://bbus-project.onrender.com/api/routes_for_display_for_history_for_history_for_history_for_history_for_history_for_history_for_history_for_history_for_history_for_history/${encodeURIComponent(company)}`)
        .then(response => response.json())
        .then(data => {
            const routes = data.routes;
            const select = document.getElementById('route');
            
            select.innerHTML = '';
            routes.forEach(route => {
                const option = document.createElement('option');
                option.value = route.id;
                option.textContent = route.text;
                select.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Ошибка при получении списка маршрутов для отображения для истории для истории для истории для истории для истории для истории для истории:', error);
        });
}

function getRouteTextsForDisplayForHistoryForHistoryForHistoryForHistoryForHistoryForHistoryForHistory() {
    const company = document.getElementById('company').value;
    fetch(`https://bbus-project.onrender.com/api/route_texts_for_display_for_history_for_history_for_history_for_history_for_history_for_history_for_history_for_history/${encodeURIComponent(company)}`)
        .then(response => response.json())
        .then(data => {
            const routeTexts = data.route_texts;
            const select = document.getElementById('route');
            
            select.innerHTML = '';
            routeTexts.forEach(route => {
                const option = document.createElement('option');
                option.value = route.id;
                option.textContent = route.text;
                select.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Ошибка при получении текстовых описаний маршрутов для отображения для истории для истории для истории для истории для истории для истории для истории для истории:', error);
        });
}

function getHistoryRoutesForDisplayForHistoryForHistoryForHistoryForHistoryForHistoryForHistory() {
    const company = document.getElementById('company').value;
    fetch(`https://bbus-project.onrender.com/api/history_routes_for_display_for_history_for_history_for_history_for_history_for_history_for_history_for_history_for_history/${encodeURIComponent(company)}`)
        .then(response => response.json())
        .then(data => {
            const routes = data.routes;
            const select = document.getElementById('history-route');
            
            select.innerHTML = '';
            routes.forEach(route => {
                const option = document.createElement('option');
                option.value = route.id;
                option.textContent = route.text;
                select.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Ошибка при получении списка маршрутов для истории для отображения для истории для истории для истории для истории для истории для истории для истории:', error);
        });
}