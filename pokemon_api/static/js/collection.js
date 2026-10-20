(() => {
  const cards = [...document.querySelectorAll('[data-pokemon-card]')];
  const search = document.querySelector('#collectionSearch');
  const type = document.querySelector('#typeFilter');
  const trainer = document.querySelector('#trainerFilter');
  const city = document.querySelector('#cityFilter');
  const favorites = document.querySelector('#favoritesFilter');
  const count = document.querySelector('#collectionCount');
  const empty = document.querySelector('#filteredEmpty');
  let onlyFavorites = false;

  const normalize = (value) => (value || '').trim().toLowerCase();

  function applyFilters() {
    const term = normalize(search?.value);
    const typeValue = normalize(type?.value);
    const trainerValue = normalize(trainer?.value);
    const cityValue = normalize(city?.value);
    let visible = 0;

    cards.forEach((card) => {
      const searchable = `${card.dataset.name} ${card.dataset.number}`;
      const types = normalize(card.dataset.types).split(',').filter(Boolean);
      const matches =
        (!term || searchable.includes(term)) &&
        (!typeValue || types.includes(typeValue)) &&
        (!trainerValue || normalize(card.dataset.trainer) === trainerValue) &&
        (!cityValue || normalize(card.dataset.city) === cityValue) &&
        (!onlyFavorites || card.dataset.favorite === 'true');

      card.hidden = !matches;
      if (matches) visible += 1;
    });

    if (count) count.textContent = visible;
    if (empty) empty.hidden = visible !== 0;
  }

  [search, type, trainer, city].forEach((control) => {
    control?.addEventListener(control.tagName === 'INPUT' ? 'input' : 'change', applyFilters);
  });

  favorites?.addEventListener('click', () => {
    onlyFavorites = !onlyFavorites;
    favorites.classList.toggle('active', onlyFavorites);
    favorites.setAttribute('aria-pressed', String(onlyFavorites));
    favorites.innerHTML = `${onlyFavorites ? '♥' : '♡'} Favoritos`;
    applyFilters();
  });
})();
