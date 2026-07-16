import os
import re
import csv
from datetime import datetime
from bs4 import BeautifulSoup


class PlayerParser:
    def __init__(self, html_content):
        self.soup = BeautifulSoup(html_content, 'html.parser')
        self.data = {}

    def _get_text(self, tag, default=''):
        return tag.get_text(strip=True) if tag else default

    def parse(self):
        name_tag = self.soup.find('h1')
        self.data['full_name'] = self._get_text(name_tag)

        info_div = self.soup.find('div', id='info')
        if not info_div:
            return self.data

        info_text = info_div.get_text(separator='\n')

        patterns = {
            'position': r'Position:\s*(.*?)(?:\s*▪|$|\n)',
            'shoots': r'Shoots:\s*(.*?)(?:\s*▪|$|\n)',
            'college': r'College:\s*(.*?)(?:\n|$)',
            'high_school': r'High School:\s*(.*?)(?:\n|$)',
            'draft': r'Draft:\s*(.*?)(?:\n|$)',
            'current_team': r'Current Team:\s*(.*?)(?:\n|$)',
            'pronunciation': r'Pronunciation:\s*(.*?)(?:\n|$)',
        }
        for key, pattern in patterns.items():
            match = re.search(pattern, info_text, re.IGNORECASE)
            self.data[key] = match.group(1).strip() if match else ''
            if self.data[key]:
                self.data[key] = re.sub(r'\s+', ' ', self.data[key])

        nickname_match = re.search(r'\(([^)]+)\)', info_text)
        self.data['nickname'] = nickname_match.group(1) if nickname_match else ''
        if not self.data['nickname']:
            nick_tag = self.soup.find('span', class_='nickname')
            if nick_tag:
                self.data['nickname'] = self._get_text(nick_tag)
        if not self.data['nickname'] and name_tag:
            match = re.search(r'\(([^)]+)\)', name_tag.get_text())
            if match:
                self.data['nickname'] = match.group(1)

        birth_span = self.soup.find('span', id='necro-birth')
        if birth_span and birth_span.get('data-birth'):
            birth_date_str = birth_span.get('data-birth')
            try:
                birth_dt = datetime.strptime(birth_date_str, '%Y-%m-%d')
                self.data['birth_year'] = birth_dt.year
                self.data['age'] = datetime.now().year - birth_dt.year
                # born را از متن خود span یا info بگیریم
                born_match = re.search(r'Born:\s*(.*?)(?:\s*\(|$|\n)', info_text, re.IGNORECASE)
                self.data['born'] = born_match.group(1).strip() if born_match else self._get_text(birth_span)
                if self.data['born'] and not re.search(r'\d{4}', self.data['born']):
                    self.data['born'] = f"{self.data['born']}, {birth_dt.year}"
            except ValueError:
                self._parse_born_from_info(info_text)
        else:
            self._parse_born_from_info(info_text)

        self.data['nationality'] = self._extract_nationality(self.data.get('born', ''))

        self._parse_height_weight(info_div)

        meta_div = self.soup.find('div', id='meta')
        if meta_div:
            img = meta_div.find('img')
            self.data['photo_url'] = img.get('src') if img and img.get('src') else ''
        else:
            self.data['photo_url'] = ''

        for k, v in self.data.items():
            if isinstance(v, str):
                self.data[k] = v.strip()

        return self.data

    def _parse_born_from_info(self, info_text):
        match = re.search(r'Born:\s*(.*?)(?:\s*\(|$|\n)', info_text, re.IGNORECASE)
        if match:
            born_raw = match.group(1).strip()
            self.data['born'] = born_raw
            year_match = re.search(r'\b(\d{4})\b', born_raw)
            self.data['birth_year'] = int(year_match.group(1)) if year_match else ''
            self.data['age'] = datetime.now().year - int(year_match.group(1)) if year_match else ''
        else:
            self.data['born'] = ''
            self.data['birth_year'] = ''
            self.data['age'] = ''

    def _extract_nationality(self, born_text):
        if not born_text:
            return ''
        parts = [p.strip() for p in born_text.split(',')]
        if len(parts) >= 2:
            last = parts[-1]
            if re.match(r'^[a-z]{2}$', last):
                return last.upper()
            return last
        return ''

    def _parse_height_weight(self, info_div):
        p_tags = info_div.find_all('p')
        for p in p_tags:
            spans = p.find_all('span')
            if len(spans) >= 2:
                height_span = spans[0].get_text(strip=True) if len(spans) > 0 else ''
                weight_span = spans[1].get_text(strip=True) if len(spans) > 1 else ''
               
                metric_span = spans[2].get_text(strip=True) if len(spans) > 2 else ''

                
                self.data['height_display'] = height_span
                self.data['weight_display'] = weight_span

                # inch to cm
                self.data['height_inches'] = self._parse_height_inches(height_span)
                self.data['height_cm'] = self._parse_height_cm(height_span, metric_span)

                # pond to kg
                self.data['weight_lbs'] = self._parse_weight_lbs(weight_span)
                self.data['weight_kg'] = self._parse_weight_kg(weight_span, metric_span)


                self.data['height'] = height_span
                self.data['weight'] = weight_span
                break  # فقط اولین پاراگراف مناسب را بگیر

        
        if 'height_display' not in self.data:
            self._fallback_parse_height_weight(info_div.get_text(separator='\n'))

    def _fallback_parse_height_weight(self, info_text):
        # for seperat use regex
        match = re.search(r'(\d+-\d+)\s*,\s*(\d+)\s*(?:lbs?|lb|pounds?)\s*\((\d+)\s*cm,\s*(\d+)\s*kg\)', info_text, re.IGNORECASE)
        if match:
            self.data['height_display'] = match.group(1)
            self.data['weight_display'] = match.group(2) + 'lb'
            self.data['height_inches'] = self._parse_height_inches(match.group(1))
            self.data['height_cm'] = int(match.group(3))
            self.data['weight_lbs'] = int(match.group(2))
            self.data['weight_kg'] = int(match.group(4))
            self.data['height'] = match.group(1)
            self.data['weight'] = match.group(2) + 'lb'
        else:
            # use easy way
            h_match = re.search(r'(\d+)-(\d+)', info_text)
            if h_match:
                self.data['height_display'] = f"{h_match.group(1)}-{h_match.group(2)}"
                self.data['height_inches'] = int(h_match.group(1))*12 + int(h_match.group(2))
                self.data['height_cm'] = round(self.data['height_inches'] * 2.54)
            w_match = re.search(r'(\d+)\s*(?:lbs?|lb|pounds?)', info_text, re.IGNORECASE)
            if w_match:
                self.data['weight_display'] = w_match.group(1) + 'lb'
                self.data['weight_lbs'] = int(w_match.group(1))
                self.data['weight_kg'] = round(int(w_match.group(1)) / 2.20462)

    def _parse_height_inches(self, height_str):
        if not height_str:
            return ''
        match = re.search(r'(\d+)-(\d+)', height_str)
        if match:
            return int(match.group(1))*12 + int(match.group(2))
        if height_str.isdigit():
            return int(height_str)
        return ''

    def _parse_height_cm(self, height_span, metric_span):
        if metric_span:
            cm_match = re.search(r'(\d+)\s*cm', metric_span, re.IGNORECASE)
            if cm_match:
                return int(cm_match.group(1))
            
        inches = self._parse_height_inches(height_span)
        if inches:
            return round(inches * 2.54)
        return ''

    def _parse_weight_lbs(self, weight_span):
        if not weight_span:
            return ''
        match = re.search(r'(\d+)', weight_span)
        if match:
            return int(match.group(1))
        return ''

    def _parse_weight_kg(self, weight_span, metric_span):
        if metric_span:
            kg_match = re.search(r'(\d+)\s*kg', metric_span, re.IGNORECASE)
            if kg_match:
                return int(kg_match.group(1))
            
        lbs = self._parse_weight_lbs(weight_span)
        if lbs:
            return round(lbs / 2.20462)
        return ''


def process_players(gamers_dir, output_file='players.csv'):
    all_players = []
    count = 0
    total_files = len([f for f in os.listdir(gamers_dir) if f.endswith('.html')])
    for filename in os.listdir(gamers_dir):
        if filename.endswith('.html'):
            count += 1
            # if count == 100 :
            #     break
            filepath = os.path.join(gamers_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                html = f.read()
            parser = PlayerParser(html)
            data = parser.parse()
            data['file'] = filename
            all_players.append(data)
            print(f"[{count}/{total_files}] Processed player: {data.get('full_name', filename)}")
    
    if not all_players:
        print("No player files found.")
        return
    
    fieldnames = ['full_name', 'nickname', 'position', 'shoots', 'born', 'age',
                  'nationality', 'height', 'height_inches', 'weight', 'weight_lbs',
                  'college', 'high_school', 'draft', 'current_team', 'pronunciation',
                  'photo_url', 'file']
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for player in all_players:
            if not player.get('age') and player.get('born'):
                birth_str = player.get('born', '')
                if birth_str:
                    year_match = re.search(r'\b(\d{4})\b', birth_str)
                    if year_match:
                        birth_year = int(year_match.group(1))
                        player['age'] = datetime.now().year - birth_year
            writer.writerow(player)
    print(f"Players saved to {output_file}")



def main():
    gamers_dir = "basketball_pages/gamers"
    clubs_dir = "basketball_pages/clubs"
    if not os.path.exists(gamers_dir):
        print(f"Gamers directory '{gamers_dir}' not found.")
        return
    if not os.path.exists(clubs_dir):
        print(f"Clubs directory '{clubs_dir}' not found.")
        return

    process_players(gamers_dir, "players.csv")
    process_clubs(clubs_dir, "clubs.csv", season="2026")
    print("Data extraction complete.")

if __name__ == "__main__":
    main()
