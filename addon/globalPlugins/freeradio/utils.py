# -*- coding: utf-8 -*-
# FreeRadio - Shared utilities
#
# Helper functions shared across multiple modules:
#   - Country code → country name translation (multi-language, NVDA gettext-aware)
#   - Station label / first-tag helpers
#   - Turkish alphabetical sort key

import addonHandler
addonHandler.initTranslation()
_tr = globals()["_"]
_ = _tr
del _tr


# ---------------------------------------------------------------------------
# Country names — static Turkish fallback dictionary
#
# Resolution order (see country_name function):
#   1. Try the gettext-translated name for NVDA's active language.
#      Every country name is marked with a separate _() call so xgettext
#      picks them up automatically.
#   2. If no translation exists (msgid == msgstr), fall back to the Turkish
#      static dictionary below.
#   3. If still not found, return the ISO code as-is.
#
# To add a new language, only translate the msgids listed in
# locale/<lang>/LC_MESSAGES/nvda.po — no changes to this file are needed.
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


# English msgid → Turkish static fallback mapping.
# _() is evaluated on every call, so language switches take effect immediately.
# When a .po file provides a translation for a msgid, that translation is used;
# otherwise the English msgid is returned (NVDA's default behaviour).
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


# Reverse mapping: display name → ISO code.
# Built from both dictionaries (Turkish + English) so that a code can be
# looked up regardless of which language is currently displayed.
_NAME_TO_CODE: dict[str, str] = {v: k for k, v in _COUNTRY_NAMES.items()}
_NAME_TO_CODE.update({v: k for k, v in _COUNTRY_MSGID.items()})


def country_name(code: str) -> str:
	"""Return the country name for the given ISO 3166-1 alpha-2 code in NVDA's active language.

	Resolution order:
	  1. gettext translation from a .po file (msgid != translated string)
	  2. Turkish static dictionary when NVDA's language is Turkish
	  3. English msgid (international standard) for all other languages
	  4. The ISO code itself if nothing else matches
	"""
	if not code:
		return code
	upper = code.strip().upper()

	# 1. gettext .po translation
	msgid = _COUNTRY_MSGID.get(upper)
	if msgid:
		translated = _(msgid)
		if translated != msgid:
			return translated

	# Retrieve the active NVDA language
	try:
		import languageHandler
		lang = languageHandler.getLanguage() or "en"
	except Exception:
		lang = "en"

	# 2. Turkish static dictionary
	if lang.startswith("tr"):
		return _COUNTRY_NAMES.get(upper, msgid or upper)

	# 3. English msgid
	if msgid:
		return msgid

	# 4. ISO code
	return upper


def name_to_code(display_name: str) -> str:
	"""Return the ISO code for a country name as currently displayed.

	Works regardless of which language the name is shown in:
	  1. Static lookup tables (Turkish + English)
	  2. gettext .po translation
	  3. Return display_name unchanged if no match is found
	"""
	if not display_name:
		return display_name

	# 1. Static lookup tables
	code = _NAME_TO_CODE.get(display_name)
	if code:
		return code

	# 2. .po translation
	for iso, msgid in _COUNTRY_MSGID.items():
		if _(msgid) == display_name:
			return iso

	# 3. Not found
	return display_name


# ---------------------------------------------------------------------------
# Station label / tag helpers
# ---------------------------------------------------------------------------

def station_label(station: dict) -> str:
	"""Return the full display label for a station list entry: Name - Country - First tag."""
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
	"""Return the station's first tag in lower case, or an empty string if none."""
	tags = station.get("tags", "")
	if not tags:
		return ""
	return tags.split(",")[0].strip().lower()


# ---------------------------------------------------------------------------
# Turkish alphabetical sort key
# ---------------------------------------------------------------------------

# Turkish character order (İ/i, Ğ/ğ, Ş/ş, Ü/ü, Ö/ö, Ç/ç differ from English)
_TR_ORDER = "aAbBcCçÇdDeEfFgGğĞhHıIiİjJkKlLmMnNoOöÖpPrRsSSşŞtTuUüÜvVyYzZ0123456789"
_TR_CHAR_KEY: dict[str, int] = {ch: idx for idx, ch in enumerate(_TR_ORDER)}


def normalize_for_search(text: str) -> str:
	"""Lower-case text and fold Turkish characters to their ASCII equivalents for searching."""
	if not text:
		return ""
	text = text.lower()
	mapping = {
		"ç": "c", "ğ": "g", "ı": "i", "i̇": "i", "ö": "o", "ş": "s", "ü": "u",
		"â": "a", "î": "i", "û": "u"
	}
	for k, v in mapping.items():
		text = text.replace(k, v)
	return text

def matches_query(station: dict, query: str) -> bool:
	"""Return True when every space-separated token in query appears in the station data."""
	query = query.strip()
	if not query:
		return True

	# Normalise both the query and the haystack: fold Turkish characters to ASCII
	# equivalents and convert to lower case.
	tokens = normalize_for_search(query).split()

	# bitrate is numeric (e.g. 128, 320) and often 0/missing when the station
	# doesn't report one - only add it to the haystack when it's a real,
	# positive value, so an empty/unknown bitrate never contributes a
	# spurious "0" token that could accidentally match unrelated searches.
	bitrate = station.get("bitrate", 0)
	try:
		bitrate = int(bitrate)
	except (TypeError, ValueError):
		bitrate = 0

	haystack = " ".join([
		station.get("name", ""),
		station.get("countrycode", ""),
		country_name(station.get("countrycode", "")),
		station.get("tags", ""),
		station.get("language", ""),
		station.get("codec", ""),
		str(bitrate) if bitrate > 0 else "",
	])
	haystack = normalize_for_search(haystack)

	# Every token must appear somewhere in the haystack (AND semantics).
	for token in tokens:
		if token not in haystack:
			return False
	return True


def tr_sort_key(station: dict) -> list[int]:
	"""Generates Turkish alphabetical sorting key from the station name."""
	name = station.get("name", "").strip()
	return [_TR_CHAR_KEY.get(ch, len(_TR_ORDER) + ord(ch)) for ch in name]