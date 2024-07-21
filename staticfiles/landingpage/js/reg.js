
document.addEventListener('DOMContentLoaded', function() {
  const stateField = document.querySelector('select[name="state"]');
  const lgaField = document.querySelector('select[name="lga"]');

  stateField.addEventListener('change', function() {
    const state = stateField.value;

    fetch(`/get-lgas/?state=${state}`)
      .then(response => response.json())
      .then(data => {
        lgaField.innerHTML = '';
        data.lgas.forEach(function(lga) {
          const option = document.createElement('option');
          option.value = lga;
          option.text = lga;
          lgaField.appendChild(option);
        });
      });
  });
});

