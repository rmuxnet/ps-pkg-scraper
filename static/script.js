const form = document.getElementById('search-form');
const input = document.getElementById('query-input');
const resultsSection = document.getElementById('results-section');
const resultsGrid = document.getElementById('results-grid');
const loader = document.getElementById('loader');
const countLabel = document.getElementById('result-count');

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
            const card = document.createElement('a');
            card.href = "#";
            card.className = "block border border-border bg-offblack p-6 hover:border-white transition group relative overflow-hidden";
            
            const bgImage = game.image ? `url('${game.image}')` : 'none';

            card.innerHTML = `
                <div class="flex justify-between items-start mb-4 relative z-10">
                    <h3 class="text-white font-bold text-lg leading-tight group-hover:underline decoration-1 underline-offset-4 pr-4">${game.title}</h3>
                    <span class="text-[10px] border border-border bg-black rounded px-2 py-1 text-dim tracking-wider shrink-0">PKG</span>
                </div>
                
                <div class="flex gap-4 mb-4 relative z-10">
                    <div class="w-16 h-16 bg-cover bg-center border border-border shrink-0" style="background-image: ${bgImage}; background-color: #111;"></div>
                    <div class="text-xs text-terminal space-y-1 font-mono">
                        <p><span class="text-dim">SIZE:</span> ${game.size || 'Unknown'}</p>
                        <p><span class="text-dim">REGION:</span> ${game.region || 'Global'}</p>
                        <p><span class="text-dim">ID:</span> ${game.cusa || 'N/A'}</p>
                    </div>
                </div>

                <div class="text-xs text-dim font-mono border-t border-border pt-3 mt-2 flex justify-between items-center relative z-10">
                    <span>> STATUS: READY</span>
                    <span class="text-white group-hover:translate-x-1 transition-transform">Get links -></span>
                </div>
                
                <div class="absolute inset-0 bg-white opacity-0 group-hover:opacity-5 pointer-events-none transition-opacity"></div>
            `;

            card.addEventListener('click', (ev) => {
                ev.preventDefault();
                fetchDetails(game.url, card);
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
    cardElement.innerHTML = `<div class="h-32 flex items-center justify-center text-dim animate-blink">Meow...</div>`;
    
    try {
        const res = await fetch(`/details?url=${encodeURIComponent(url)}`);
        if(!res.ok) throw new Error("Fetch failed");
        const data = await res.json();
        
        let linksHtml = '';
        if(data.links) {
            const links = Array.isArray(data.links) ? data.links : [];
            links.forEach(linkItem => {
                const href = typeof linkItem === 'string' ? linkItem : linkItem.url;
                const label = typeof linkItem === 'string' ? 'Download' : (linkItem.label || 'Link');
                const group = typeof linkItem === 'string' ? 'Mirror' : (linkItem.group || 'Misc');
                
                linksHtml += `
                    <li class="flex justify-between items-center border-b border-border py-2 text-xs">
                        <span class="text-dim">[${group}] ${label}</span>
                        <a href="${href}" target="_blank" class="text-white hover:text-green-400 hover:underline truncate ml-4 max-w-[150px]">> Open URL</a>
                    </li>
                `;
            });
        }

        cardElement.classList.remove('hover:border-white');
        cardElement.classList.add('border-dim');
        cardElement.innerHTML = `
            <div class="mb-3 border-b border-border pb-2 flex justify-between">
                    <span class="text-white font-bold">Data Extracted</span>
                    <button onclick="event.stopPropagation(); resetCard(this)" class="text-red-500 hover:text-red-400 text-xs">[CLOSE]</button>
            </div>
            <div class="space-y-2 mb-4">
                <div class="flex justify-between text-xs"><span class="text-dim">FW:</span> <span class="text-terminal">${data.metadata.firmware || 'N/A'}</span></div>
                <div class="flex justify-between text-xs"><span class="text-dim">Pass:</span> <span class="text-red-400 select-all">${data.metadata.password || 'N/A'}</span></div>
            </div>
            <ul class="max-h-40 overflow-y-auto pr-2 custom-scrollbar">
                ${linksHtml || '<li class="text-dim text-xs">No links found</li>'}
            </ul>
        `;
        
        cardElement.dataset.original = originalText;

    } catch (err) {
        alert("Failed to load details.");
        cardElement.innerHTML = originalText;
    }
}

window.resetCard = function(btn) {
    const card = btn.closest('a');
    if(card && card.dataset.original) {
        card.innerHTML = card.dataset.original;
        card.classList.add('hover:border-white');
        card.classList.remove('border-dim');
    }
}