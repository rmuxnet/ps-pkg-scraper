from bs4 import BeautifulSoup
import re

def parse_metadata(soup, metadata):
	tables = soup.find_all("table")
	for table in tables:
		rows = table.find_all("tr")
		for row in rows:
			cols = row.find_all("td")
			if len(cols) >= 2:
				key_raw = cols[0].get_text(strip=True, separator=" ").lower()
				key = re.sub(r'[^\w\s]', '', key_raw).strip()
				val = cols[1].get_text(strip=True, separator=" ")
				
				if "size" in key or "tamanho" in key:
					metadata["size"] = val
				elif "password" in key or "senha" in key:
					metadata["password"] = val
				elif "version" in key or "versão" in key:
					if val.lower() != "n/a":
						clean_ver = re.sub(r'(?i)thanks?.*', '', val).strip()
						clean_ver = re.sub(r'[\u200b-\u200d\uFEFF]', '', clean_ver)
						
						curr_ver = metadata.get("version", "N/A")
						if curr_ver == "N/A":
							metadata["version"] = clean_ver
						elif clean_ver not in curr_ver:
							metadata["version"] = f"{curr_ver} | {clean_ver}"
					
					ids = re.findall(r'((?:CUSA|PPSA)\d{5})', val, re.IGNORECASE)
					for mid in ids:
						mid = mid.upper()
						curr_cusa = metadata.get("cusa", "N/A")
						if curr_cusa == "N/A":
							metadata["cusa"] = mid
						elif mid not in curr_cusa:
							metadata["cusa"] = f"{curr_cusa}, {mid}"
					
					found_region = None
					if "USA" in val:
						found_region = "USA"
					elif "EUR" in val:
						found_region = "EUR"
					elif "JPN" in val:
						found_region = "JPN"
					elif "ASIA" in val:
						found_region = "ASIA"
					
					if found_region:
						curr_reg = metadata.get("region", "N/A")
						if curr_reg == "N/A":
							metadata["region"] = found_region
						elif found_region not in curr_reg:
							metadata["region"] = f"{curr_reg}, {found_region}"

				elif "voice" in key:
					if metadata["voice"] == "N/A":
						metadata["voice"] = val
				elif "subtitles" in key or "screen languages" in key:
					if metadata["subtitles"] == "N/A":
						metadata["subtitles"] = val
				elif "firmware" in key or "working" in key or "note" in key:
					if "working" in val.lower() or re.search(r'\d+\.xx', val) or re.search(r'\d+\.\d+', val):
						metadata["firmware"] = val
	return metadata
