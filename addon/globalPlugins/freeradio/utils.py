# -*- coding: utf-8 -*-
# FreeRadio - Shared utilities
#
# Bu modül birden fazla modül tarafından kullanılan yardımcı işlevleri içerir:
#   - Ülke kodu → ülke adı çevirisi (çok dilli, NVDA gettext destekli)
#   - İstasyon etiketi / ilk etiket yardımcıları
#   - Türkçe alfabetik sıralama anahtarı

import addonHandler
addonHandler.initTranslation()
_tr = globals()["_"]
_ = _tr
del _tr


# ---------------------------------------------------------------------------
# Ülke adları — statik Türkçe yedek sözlük
#
# Çalışma mantığı (country_name fonksiyonu):
#   1. NVDA'nın aktif diline göre gettext aracılığıyla çevrilmiş adı dener.
#      Bunun için her ülke adı ayrı bir _() çağrısıyla işaretlenmiştir
#      (xgettext bu satırları otomatik toplar).
#   2. Çeviri bulunamazsa (msgid == msgstr) Türkçe sözlüğe düşer.
#   3. Sözlükte de yoksa ISO kodu olduğu gibi döner.
#
# Yeni bir dil eklemek için yalnızca locale/<lang>/LC_MESSAGES/nvda.po
# dosyasına aşağıdaki msgid'leri çevirmek yeterlidir; bu dosyada değişiklik
# gerekmez.
# ---------------------------------------------------------------------------

# fmt: off
_COUNTRY_NAMES: dict[str, str] = {
	"AD": "Andorra",           "AE": "Birleşik Arap Emirlikleri", "AF": "Afganistan",
	"AG": "Antigua ve Barbuda","AI": "Anguilla",                   "AL": "Arnavutluk",
	"AM": "Ermenistan",        "AO": "Angola",                     "AQ": "Antarktika",
	"AR": "Arjantin",          "AS": "Amerikan Samoası",           "AT": "Avusturya",
	"AU": "Avustralya",        "AW": "Aruba",                      "AX": "Åland Adaları",
	"AZ": "Azerbaycan",        "BA": "Bosna-Hersek",               "BB": "Barbados",
	"BD": "Bangladeş",         "BE": "Belçika",                    "BF": "Burkina Faso",
	"BG": "Bulgaristan",       "BH": "Bahreyn",                    "BI": "Burundi",
	"BJ": "Benin",             "BL": "Saint-Barthélemy",           "BM": "Bermuda",
	"BN": "Brunei",            "BO": "Bolivya",                    "BQ": "Karayip Hollandası",
	"BR": "Brezilya",          "BS": "Bahamalar",                  "BT": "Bhutan",
	"BV": "Bouvet Adası",      "BW": "Botsvana",                   "BY": "Beyaz Rusya",
	"BZ": "Belize",            "CA": "Kanada",                     "CC": "Cocos Adaları",
	"CD": "Kongo (Demokratik Cumhuriyet)",                          "CF": "Orta Afrika Cumhuriyeti",
	"CG": "Kongo",             "CH": "İsviçre",                    "CI": "Fildişi Sahili",
	"CK": "Cook Adaları",      "CL": "Şili",                       "CM": "Kamerun",
	"CN": "Çin",               "CO": "Kolombiya",                  "CR": "Kosta Rika",
	"CU": "Küba",              "CV": "Yeşil Burun Adaları",        "CW": "Curaçao",
	"CX": "Christmas Adası",   "CY": "Kıbrıs",                     "CZ": "Çekya",
	"DE": "Almanya",           "DJ": "Cibuti",                     "DK": "Danimarka",
	"DM": "Dominika",          "DO": "Dominik Cumhuriyet",         "DZ": "Cezayir",
	"EC": "Ekvador",           "EE": "Estonya",                    "EG": "Mısır",
	"EH": "Batı Sahra",        "ER": "Eritre",                     "ES": "İspanya",
	"ET": "Etiyopya",          "FI": "Finlandiya",                 "FJ": "Fiji",
	"FK": "Falkland Adaları",  "FM": "Mikronezya",                 "FO": "Faroe Adaları",
	"FR": "Fransa",            "GA": "Gabon",                      "GB": "Birleşik Krallık",
	"GD": "Grenada",           "GE": "Gürcistan",                  "GF": "Fransız Guyanası",
	"GG": "Guernsey",          "GH": "Gana",                       "GI": "Cebelitarık",
	"GL": "Grönland",          "GM": "Gambiya",                    "GN": "Gine",
	"GP": "Guadeloupe",        "GQ": "Ekvator Ginesi",             "GR": "Yunanistan",
	"GS": "Güney Georgia ve Sandwich Adaları",                      "GT": "Guatemala",
	"GU": "Guam",              "GW": "Gine-Bissau",                "GY": "Guyana",
	"HK": "Hong Kong",         "HM": "Heard ve McDonald Adaları",
	"HN": "Honduras",          "HR": "Hırvatistan",                "HT": "Haiti",
	"HU": "Macaristan",        "ID": "Endonezya",                  "IE": "İrlanda",
	"IL": "İsrail",            "IM": "Man Adası",                  "IN": "Hindistan",
	"IO": "Hint Okyanusu İngiliz Toprağı",                          "IQ": "Irak",
	"IR": "İran",              "IS": "İzlanda",                    "IT": "İtalya",
	"JE": "Jersey",            "JM": "Jamaika",                    "JO": "Ürdün",
	"JP": "Japonya",           "KE": "Kenya",                      "KG": "Kırgızistan",
	"KH": "Kamboçya",          "KI": "Kiribati",                   "KM": "Komorlar",
	"KN": "Saint Kitts ve Nevis",                                   "KP": "Kuzey Kore",
	"KR": "Güney Kore",        "KW": "Kuveyt",                     "KY": "Cayman Adaları",
	"KZ": "Kazakistan",        "LA": "Laos",                       "LB": "Lübnan",
	"LC": "Saint Lucia",       "LI": "Lihtenştayn",                "LK": "Sri Lanka",
	"LR": "Liberya",           "LS": "Lesotho",                    "LT": "Litvanya",
	"LU": "Lüksemburg",        "LV": "Letonya",                    "LY": "Libya",
	"MA": "Fas",               "MC": "Monako",                     "MD": "Moldova",
	"ME": "Karadağ",           "MF": "Saint-Martin",               "MG": "Madagaskar",
	"MH": "Marshall Adaları",  "MK": "Kuzey Makedonya",            "ML": "Mali",
	"MM": "Myanmar",           "MN": "Moğolistan",                 "MO": "Makao",
	"MP": "Kuzey Mariana Adaları",                                  "MQ": "Martinik",
	"MR": "Moritanya",         "MS": "Montserrat",                 "MT": "Malta",
	"MU": "Mauritius",         "MV": "Maldivler",                  "MW": "Malavi",
	"MX": "Meksika",           "MY": "Malezya",                    "MZ": "Mozambik",
	"NA": "Namibya",           "NC": "Yeni Kaledonya",             "NE": "Nijer",
	"NF": "Norfolk Adası",     "NG": "Nijerya",                    "NI": "Nikaragua",
	"NL": "Hollanda",          "NO": "Norveç",                     "NP": "Nepal",
	"NR": "Nauru",             "NU": "Niue",                       "NZ": "Yeni Zelanda",
	"OM": "Umman",             "PA": "Panama",                     "PE": "Peru",
	"PF": "Fransız Polinezyası",                                    "PG": "Papua Yeni Gine",
	"PH": "Filipinler",        "PK": "Pakistan",                   "PL": "Polonya",
	"PM": "Saint-Pierre ve Miquelon",                               "PN": "Pitcairn Adaları",
	"PR": "Porto Riko",        "PS": "Filistin",                   "PT": "Portekiz",
	"PW": "Palau",             "PY": "Paraguay",                   "QA": "Katar",
	"RE": "Réunion",           "RO": "Romanya",                    "RS": "Sırbistan",
	"RU": "Rusya",             "RW": "Ruanda",                     "SA": "Suudi Arabistan",
	"SB": "Solomon Adaları",   "SC": "Seyşeller",                  "SD": "Sudan",
	"SE": "İsveç",             "SG": "Singapur",                   "SH": "Saint Helena",
	"SI": "Slovenya",          "SJ": "Svalbard ve Jan Mayen",      "SK": "Slovakya",
	"SL": "Sierra Leone",      "SM": "San Marino",                 "SN": "Senegal",
	"SO": "Somali",            "SR": "Surinam",                    "SS": "Güney Sudan",
	"ST": "São Tomé ve Príncipe",                                   "SV": "El Salvador",
	"SX": "Sint Maarten",      "SY": "Suriye",                     "SZ": "Esvatini",
	"TC": "Turks ve Caicos Adaları",                                "TD": "Çad",
	"TF": "Fransız Güney Toprakları",                               "TG": "Togo",
	"TH": "Tayland",           "TJ": "Tacikistan",                 "TK": "Tokelau",
	"TL": "Doğu Timor",        "TM": "Türkmenistan",               "TN": "Tunus",
	"TO": "Tonga",             "TR": "Türkiye",                    "TT": "Trinidad ve Tobago",
	"TV": "Tuvalu",            "TW": "Tayvan",                     "TZ": "Tanzanya",
	"UA": "Ukrayna",           "UG": "Uganda",                     "UM": "ABD Küçük Dış Adaları",
	"US": "Amerika Birleşik Devletleri",                            "UY": "Uruguay",
	"UZ": "Özbekistan",        "VA": "Vatikan",                    "VC": "Saint Vincent ve Grenadinler",
	"VE": "Venezuela",         "VG": "Britanya Virjin Adaları",    "VI": "ABD Virjin Adaları",
	"VN": "Vietnam",           "VU": "Vanuatu",                    "WF": "Wallis ve Futuna",
	"WS": "Samoa",             "XK": "Kosova",                     "YE": "Yemen",
	"YT": "Mayotte",           "ZA": "Güney Afrika",               "ZM": "Zambiya",
	"ZW": "Zimbabve",
}
# fmt: on


# İngilizce msgid → Türkçe statik yedek eşlemesi
# _() her çağrıda çalışır, bu nedenle dil değişiklikleri anında yansır.
# .po dosyasında bu msgid'lere karşılık gelen çeviriler varsa o dil gösterilir;
# yoksa İngilizce msgid döner (NVDA'nın kendi davranışı).
_COUNTRY_MSGID: dict[str, str] = {
	"AD": "Andorra",                           "AE": "United Arab Emirates",
	"AF": "Afghanistan",                       "AG": "Antigua and Barbuda",
	"AI": "Anguilla",                          "AL": "Albania",
	"AM": "Armenia",                           "AO": "Angola",
	"AQ": "Antarctica",                        "AR": "Argentina",
	"AS": "American Samoa",                    "AT": "Austria",
	"AU": "Australia",                         "AW": "Aruba",
	"AX": "\u00c5land Islands",               "AZ": "Azerbaijan",
	"BA": "Bosnia and Herzegovina",            "BB": "Barbados",
	"BD": "Bangladesh",                        "BE": "Belgium",
	"BF": "Burkina Faso",                      "BG": "Bulgaria",
	"BH": "Bahrain",                           "BI": "Burundi",
	"BJ": "Benin",                             "BL": "Saint Barth\u00e9lemy",
	"BM": "Bermuda",                           "BN": "Brunei",
	"BO": "Bolivia",                           "BQ": "Caribbean Netherlands",
	"BR": "Brazil",                            "BS": "Bahamas",
	"BT": "Bhutan",                            "BV": "Bouvet Island",
	"BW": "Botswana",                          "BY": "Belarus",
	"BZ": "Belize",                            "CA": "Canada",
	"CC": "Cocos Islands",                     "CD": "Congo, Democratic Republic",
	"CF": "Central African Republic",          "CG": "Congo",
	"CH": "Switzerland",                       "CI": "Ivory Coast",
	"CK": "Cook Islands",                      "CL": "Chile",
	"CM": "Cameroon",                          "CN": "China",
	"CO": "Colombia",                          "CR": "Costa Rica",
	"CU": "Cuba",                              "CV": "Cape Verde",
	"CW": "Cura\u00e7ao",                     "CX": "Christmas Island",
	"CY": "Cyprus",                            "CZ": "Czech Republic",
	"DE": "Germany",                           "DJ": "Djibouti",
	"DK": "Denmark",                           "DM": "Dominica",
	"DO": "Dominican Republic",                "DZ": "Algeria",
	"EC": "Ecuador",                           "EE": "Estonia",
	"EG": "Egypt",                             "EH": "Western Sahara",
	"ER": "Eritrea",                           "ES": "Spain",
	"ET": "Ethiopia",                          "FI": "Finland",
	"FJ": "Fiji",                              "FK": "Falkland Islands",
	"FM": "Micronesia",                        "FO": "Faroe Islands",
	"FR": "France",                            "GA": "Gabon",
	"GB": "United Kingdom",                    "GD": "Grenada",
	"GE": "Georgia",                           "GF": "French Guiana",
	"GG": "Guernsey",                          "GH": "Ghana",
	"GI": "Gibraltar",                         "GL": "Greenland",
	"GM": "Gambia",                            "GN": "Guinea",
	"GP": "Guadeloupe",                        "GQ": "Equatorial Guinea",
	"GR": "Greece",                            "GS": "South Georgia and the Sandwich Islands",
	"GT": "Guatemala",                         "GU": "Guam",
	"GW": "Guinea-Bissau",                     "GY": "Guyana",
	"HK": "Hong Kong",                         "HM": "Heard and McDonald Islands",
	"HN": "Honduras",                          "HR": "Croatia",
	"HT": "Haiti",                             "HU": "Hungary",
	"ID": "Indonesia",                         "IE": "Ireland",
	"IL": "Israel",                            "IM": "Isle of Man",
	"IN": "India",                             "IO": "British Indian Ocean Territory",
	"IQ": "Iraq",                              "IR": "Iran",
	"IS": "Iceland",                           "IT": "Italy",
	"JE": "Jersey",                            "JM": "Jamaica",
	"JO": "Jordan",                            "JP": "Japan",
	"KE": "Kenya",                             "KG": "Kyrgyzstan",
	"KH": "Cambodia",                          "KI": "Kiribati",
	"KM": "Comoros",                           "KN": "Saint Kitts and Nevis",
	"KP": "North Korea",                       "KR": "South Korea",
	"KW": "Kuwait",                            "KY": "Cayman Islands",
	"KZ": "Kazakhstan",                        "LA": "Laos",
	"LB": "Lebanon",                           "LC": "Saint Lucia",
	"LI": "Liechtenstein",                     "LK": "Sri Lanka",
	"LR": "Liberia",                           "LS": "Lesotho",
	"LT": "Lithuania",                         "LU": "Luxembourg",
	"LV": "Latvia",                            "LY": "Libya",
	"MA": "Morocco",                           "MC": "Monaco",
	"MD": "Moldova",                           "ME": "Montenegro",
	"MF": "Saint Martin",                      "MG": "Madagascar",
	"MH": "Marshall Islands",                  "MK": "North Macedonia",
	"ML": "Mali",                              "MM": "Myanmar",
	"MN": "Mongolia",                          "MO": "Macau",
	"MP": "Northern Mariana Islands",          "MQ": "Martinique",
	"MR": "Mauritania",                        "MS": "Montserrat",
	"MT": "Malta",                             "MU": "Mauritius",
	"MV": "Maldives",                          "MW": "Malawi",
	"MX": "Mexico",                            "MY": "Malaysia",
	"MZ": "Mozambique",                        "NA": "Namibia",
	"NC": "New Caledonia",                     "NE": "Niger",
	"NF": "Norfolk Island",                    "NG": "Nigeria",
	"NI": "Nicaragua",                         "NL": "Netherlands",
	"NO": "Norway",                            "NP": "Nepal",
	"NR": "Nauru",                             "NU": "Niue",
	"NZ": "New Zealand",                       "OM": "Oman",
	"PA": "Panama",                            "PE": "Peru",
	"PF": "French Polynesia",                  "PG": "Papua New Guinea",
	"PH": "Philippines",                       "PK": "Pakistan",
	"PL": "Poland",                            "PM": "Saint Pierre and Miquelon",
	"PN": "Pitcairn Islands",                  "PR": "Puerto Rico",
	"PS": "Palestine",                         "PT": "Portugal",
	"PW": "Palau",                             "PY": "Paraguay",
	"QA": "Qatar",                             "RE": "R\u00e9union",
	"RO": "Romania",                           "RS": "Serbia",
	"RU": "Russia",                            "RW": "Rwanda",
	"SA": "Saudi Arabia",                      "SB": "Solomon Islands",
	"SC": "Seychelles",                        "SD": "Sudan",
	"SE": "Sweden",                            "SG": "Singapore",
	"SH": "Saint Helena",                      "SI": "Slovenia",
	"SJ": "Svalbard and Jan Mayen",            "SK": "Slovakia",
	"SL": "Sierra Leone",                      "SM": "San Marino",
	"SN": "Senegal",                           "SO": "Somalia",
	"SR": "Suriname",                          "SS": "South Sudan",
	"ST": "S\u00e3o Tom\u00e9 and Pr\u00edncipe",  "SV": "El Salvador",
	"SX": "Sint Maarten",                      "SY": "Syria",
	"SZ": "Eswatini",                          "TC": "Turks and Caicos Islands",
	"TD": "Chad",                              "TF": "French Southern Territories",
	"TG": "Togo",                              "TH": "Thailand",
	"TJ": "Tajikistan",                        "TK": "Tokelau",
	"TL": "East Timor",                        "TM": "Turkmenistan",
	"TN": "Tunisia",                           "TO": "Tonga",
	"TR": "Turkey",                            "TT": "Trinidad and Tobago",
	"TV": "Tuvalu",                            "TW": "Taiwan",
	"TZ": "Tanzania",                          "UA": "Ukraine",
	"UG": "Uganda",                            "UM": "US Minor Outlying Islands",
	"US": "United States",                     "UY": "Uruguay",
	"UZ": "Uzbekistan",                        "VA": "Vatican City",
	"VC": "Saint Vincent and the Grenadines",  "VE": "Venezuela",
	"VG": "British Virgin Islands",            "VI": "US Virgin Islands",
	"VN": "Vietnam",                           "VU": "Vanuatu",
	"WF": "Wallis and Futuna",                 "WS": "Samoa",
	"XK": "Kosovo",                            "YE": "Yemen",
	"YT": "Mayotte",                           "ZA": "South Africa",
	"ZM": "Zambia",                            "ZW": "Zimbabwe",
}


# İsim → kod ters eşlemesi
# Her iki sözlükten de (Türkçe + İngilizce) eşleme yapılır; böylece
# hangi dilde görünüyorsa o isimden kod bulunabilir.
_NAME_TO_CODE: dict[str, str] = {v: k for k, v in _COUNTRY_NAMES.items()}
_NAME_TO_CODE.update({v: k for k, v in _COUNTRY_MSGID.items()})


def country_name(code: str) -> str:
	"""ISO 3166-1 alpha-2 kodundan aktif NVDA diline göre ülke adını döner.

	Öncelik sırası:
	  1. .po dosyasında çeviri varsa (msgid != çeviri) → gettext sonucu
	  2. NVDA dili Türkçe ise → _COUNTRY_NAMES statik sözlüğü
	  3. Diğer dillerde → İngilizce msgid (uluslararası standart)
	  4. Hiçbiri bulunamazsa → ISO kodu
	"""
	if not code:
		return code
	upper = code.strip().upper()

	# 1. gettext .po çevirisi
	msgid = _COUNTRY_MSGID.get(upper)
	if msgid:
		translated = _(msgid)
		if translated != msgid:
			return translated

	# NVDA dilini al
	try:
		import languageHandler
		lang = languageHandler.getLanguage() or "en"
	except Exception:
		lang = "en"

	# 2. Türkçe statik sözlük
	if lang.startswith("tr"):
		return _COUNTRY_NAMES.get(upper, msgid or upper)

	# 3. İngilizce msgid
	if msgid:
		return msgid

	# 4. ISO kodu
	return upper


def name_to_code(display_name: str) -> str:
	"""Ekranda gösterilen ülke adından ISO kodunu döner.

	Hangi dilde görünüyorsa o addan koda çevirir:
	  1. Statik tablolar (Türkçe + İngilizce)
	  2. .po gettext çevirisi
	  3. Bulunamazsa display_name olduğu gibi döner
	"""
	if not display_name:
		return display_name

	# 1. Statik tablolar
	code = _NAME_TO_CODE.get(display_name)
	if code:
		return code

	# 2. .po çevirisi
	for iso, msgid in _COUNTRY_MSGID.items():
		if _(msgid) == display_name:
			return iso

	# 3. Bulunamadı
	return display_name


# ---------------------------------------------------------------------------
# İstasyon etiket / etiket yardımcıları
# ---------------------------------------------------------------------------

def station_label(station: dict) -> str:
	"""İstasyon listesinde gösterilecek tam etiketi döner: Ad - Ülke - İlk etiket."""
	name    = station.get("name", _("Unknown"))
	country = station.get("countrycode", "")
	tags    = station.get("tags", "")
	parts   = [name.strip()]
	if country:
		parts.append(country_name(country))
	if tags:
		first_tag = tags.split(",")[0].strip()
		if first_tag:
			parts.append(first_tag)
	return " - ".join(parts)


def first_tag(station: dict) -> str:
	"""İstasyonun ilk etiketini küçük harfle döner; yoksa boş string."""
	tags = station.get("tags", "")
	if not tags:
		return ""
	return tags.split(",")[0].strip().lower()


# ---------------------------------------------------------------------------
# Türkçe alfabetik sıralama
# ---------------------------------------------------------------------------

# Türkçe karakter sırası (İ/i, Ğ/ğ, Ş/ş, Ü/ü, Ö/ö, Ç/ç İngilizce'den farklı)
_TR_ORDER = "aAbBcCçÇdDeEfFgGğĞhHıIiİjJkKlLmMnNoOöÖpPrRsSSşŞtTuUüÜvVyYzZ0123456789"
_TR_CHAR_KEY: dict[str, int] = {ch: idx for idx, ch in enumerate(_TR_ORDER)}


def tr_sort_key(station: dict) -> list[int]:
	"""İstasyon adından Türkçe alfabetik sıralama anahtarı üretir."""
	name = station.get("name", "").strip()
	return [_TR_CHAR_KEY.get(ch, len(_TR_ORDER) + ord(ch)) for ch in name]