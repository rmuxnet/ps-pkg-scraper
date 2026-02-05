const form = document.getElementById('search-form');
const input = document.getElementById('query-input');
const resultsSection = document.getElementById('results-section');
const resultsGrid = document.getElementById('results-grid');
const loader = document.getElementById('loader');
const countLabel = document.getElementById('result-count');

const templates = {};

async function loadTemplates() {
    const files = ['card_result', 'card_details', 'link_item'];
    try {
        await Promise.all(files.map(async (name) => {
            const res = await fetch(`/static/res/${name}.html`);
            if(res.ok) templates[name] = await res.text();
        }));
        console.log("Templates loaded:", Object.keys(templates));
    } catch (e) {
        console.error("Failed to load templates:", e);
    }
}
loadTemplates();

function render(templateName, data) {
    let html = templates[templateName] || '';
    for (const key in data) {
        const regex = new RegExp(`{{${key}}}`, 'g');
        html = html.replace(regex, data[key] !== undefined && data[key] !== null ? data[key] : '');
    }
    return html;
}

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = input.value.trim();
    if(!query) return;

    resultsSection.classList.add('hidden');
    loader.classList.remove('hidden');
    resultsGrid.innerHTML = '';

    try {
        const res = await fetch(`/search?q=${encodeURIComponent(query)}`);
        const data = await res.json();
        
        loader.classList.add('hidden');
        resultsSection.classList.remove('hidden');
        
        const games = data.results || [];
        countLabel.innerText = `${games.length} OBJECTS FOUND`;

        if(games.length === 0) {
            resultsGrid.innerHTML = `<div class="col-span-2 text-center text-dim border border-border p-8">No Data</div>`;
            return;
        }

        games.forEach(game => {
            const card = document.createElement('div');
            card.className = "block border border-border bg-offblack p-6 hover:border-white transition group relative overflow-hidden cursor-pointer";
            
            const templateData = {
                title: game.title,
                bg_image: game.image ? `url('${game.image}')` : 'none',
                size: game.size || 'Unknown',
                region: game.region || 'Global',
                cusa: game.cusa || 'N/A'
            };

            card.innerHTML = render('card_result', templateData);

            card.addEventListener('click', (ev) => {
                if (!card.dataset.original) {
                    ev.preventDefault();
                    fetchDetails(game.url, card);
                }
            });

            resultsGrid.appendChild(card);
        });

    } catch (err) {
        console.error(err);
        loader.classList.add('hidden');
        resultsGrid.innerHTML = `<div class="col-span-2 text-red-800 font-bold text-center">Soo: ${err.message}</div>`;
        resultsSection.classList.remove('hidden');
    }
});

async function fetchDetails(url, cardElement) {
    const originalText = cardElement.innerHTML;
    cardElement.dataset.original = originalText;
    
    cardElement.innerHTML = `<div class="h-32 flex items-center justify-center text-dim animate-blink">Meow...</div>`;
    
    try {
        const res = await fetch(`/details?url=${encodeURIComponent(url)}`);
        if(!res.ok) throw new Error("Fetch failed");
        const data = await res.json();
        
        let linksHtml = '';
        if(data.links && Array.isArray(data.links)) {
            data.links.forEach(linkItem => {
                const isObj = typeof linkItem !== 'string';
                const linkData = {
                    url: isObj ? linkItem.url : linkItem,
                    label: isObj ? (linkItem.label || 'Link') : 'Download',
                    group: isObj ? (linkItem.group || 'Misc') : 'Mirror'
                };
                
                linksHtml += render('link_item', linkData);
            });
        }

        const detailsData = {
            firmware: data.metadata.firmware || 'N/A',
            password: data.metadata.password || 'N/A',
            links_list: linksHtml || '<li class="text-dim text-xs">No links found</li>'
        };

        cardElement.classList.remove('hover:border-white');
        cardElement.classList.add('border-dim');
        
        cardElement.innerHTML = render('card_details', detailsData);
        
        cardElement.dataset.original = originalText;

    } catch (err) {
        alert("Failed to load details.");
        cardElement.innerHTML = originalText;
        delete cardElement.dataset.original;
    }
}

window.resetCard = function(btn) {
    const card = btn.closest('div');
    if(card && card.dataset.original) {
        card.innerHTML = card.dataset.original;
        card.classList.add('hover:border-white');
        card.classList.remove('border-dim');
        delete card.dataset.original;
    }
}