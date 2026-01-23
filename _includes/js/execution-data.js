// Fetch and render execution client data dynamically
(function() {
  const DATA_URL = '/data/extra_data.json';

  function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
  }

  function getColorAndStatus(value) {
    if (value > 50) {
      return { color: 'danger', status: 'danger!' };
    } else if (value > 33) {
      return { color: 'warning', status: 'caution' };
    }
    return { color: 'success', status: 'great!' };
  }

  function renderProgressBar(client, round = true) {
    const name = capitalize(client.name);
    let value = client.value * 100;
    value = round ? Math.round(value) : Math.round(value * 100) / 100;
    const accuracy = client.accuracy === 'no data' ? 'no data' : (client.accuracy * 100).toFixed(1) + '%';
    const { color, status } = getColorAndStatus(value);

    return `
      <div class="my-2">
        <label class="form-label my-0 py-0">${name} - ${value}%</label>
        <div class="progress position-relative" style="height: 1rem;"
          data-bs-toggle="tooltip" data-bs-placement="top" data-bs-html="true" title='
            <div class="progress-tooltip text-capitalize text-start">
              <div class="mb-1 pb-1 text-center border-bottom border-secondary">
                ${name} status:<br>${value}% (${status})
              </div>
              <div class="d-flex justify-content-between">
                <span class="me-2">great:</span><span>0-33%</span>
              </div>
              <div class="d-flex justify-content-between">
                <span class="me-2">caution:</span><span>33-50%</span>
              </div>
              <div class="d-flex justify-content-between mb-1 pb-1 border-bottom border-secondary">
                <span class="me-2">danger:</span><span>50-100%</span>
              </div>
              <div class="d-flex justify-content-between">
                <span class="me-2">accuracy:</span><span>${accuracy}</span>
              </div>
            </div>'>
          <div class="progress-bar position-absolute bg-${color}" role="progressbar" style="width: ${value}%; height: 1.25rem;" aria-valuenow="${value}" aria-valuemin="0" aria-valuemax="100"></div>
          <div class="progress-bar bg-trans clientshare-success" role="progressbar" style="width: 33%; height: 1.25rem"></div>
          <div class="progress-bar bg-trans clientshare-warning" role="progressbar" style="width: 17%; height: 1.25rem"></div>
          <div class="progress-bar bg-trans clientshare-danger" role="progressbar" style="width: 50%; height: 1.25rem"></div>
        </div>
      </div>
    `;
  }

  function renderAlert(other) {
    const dangerClient = capitalize(other.danger_client || '');
    let alertType = other.danger_client ? 'danger' : 'info';
    let alertMsg = '';

    if (other.has_supermajority) {
      alertMsg = `${dangerClient} has a supermajority, switch to a minority client!`;
    } else if (other.has_majority) {
      alertMsg = `Switch from ${dangerClient} to a minority client!`;
    } else {
      alertMsg = 'Client diversity has improved!';
    }

    const iconSvg = other.danger_client
      ? '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-exclamation-triangle-fill flex-shrink-0 me-2" viewBox="0 0 16 16"><path d="M8.982 1.566a1.13 1.13 0 0 0-1.96 0L.165 13.233c-.457.778.091 1.767.98 1.767h13.713c.889 0 1.438-.99.98-1.767L8.982 1.566zM8 5c.535 0 .954.462.9.995l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 5.995A.905.905 0 0 1 8 5zm.002 6a1 1 0 1 1 0 2 1 1 0 0 1 0-2z"/></svg>'
      : '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-info-circle-fill flex-shrink-0 me-2" viewBox="0 0 16 16"><path d="M8 16A8 8 0 1 0 8 0a8 8 0 0 0 0 16zm.93-9.412-1 4.705c-.07.34.029.533.304.533.194 0 .487-.07.686-.246l-.088.416c-.287.346-.92.598-1.465.598-.703 0-1.002-.422-.808-1.319l.738-3.468c.064-.293.006-.399-.287-.47l-.451-.081.082-.381 2.29-.287zM8 5.5a1 1 0 1 1 0-2 1 1 0 0 1 0 2z"/></svg>';

    return `
      <a href="#why" class="extra_data execution-data text-decoration-none">
        <div class="alert alert-${alertType} d-flex align-items-center" role="alert">
          ${iconSvg}
          <div>${alertMsg}</div>
        </div>
      </a>
    `;
  }

  function renderExecutionData(data) {
    const progressContainer = document.getElementById('execution-progress-container');
    const alertContainer = document.getElementById('execution-alert-container');

    if (!progressContainer) return;

    // Get the latest data entry
    const latest = Array.isArray(data) ? data[data.length - 1] : data;

    if (!latest || !latest.data) {
      progressContainer.innerHTML = '<div class="text-center text-danger">Failed to load data</div>';
      return;
    }

    // Render progress bars
    const distribution = latest.data.distribution || [];
    progressContainer.innerHTML = distribution.map(client => renderProgressBar(client, true)).join('');

    // Render alert
    if (alertContainer && latest.data.other) {
      alertContainer.innerHTML = renderAlert(latest.data.other);
    }

    // Re-enable tooltips for new elements
    enableTooltips();
  }

  function fetchExecutionData() {
    fetch(DATA_URL)
      .then(response => {
        if (!response.ok) throw new Error('Failed to fetch data');
        return response.json();
      })
      .then(data => renderExecutionData(data))
      .catch(error => {
        console.error('Error fetching execution data:', error);
        const container = document.getElementById('execution-progress-container');
        if (container) {
          container.innerHTML = '<div class="text-center text-danger">Failed to load execution client data</div>';
        }
      });
  }

  // Fetch data when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', fetchExecutionData);
  } else {
    fetchExecutionData();
  }
})();
