# FreeRadio — NVDA Add-on NVDA
FreeRadio — កម្មវិធីជំនួយរបស់ NVDA

FreeRadio is an internet radio add-on for the NVDA screen reader. Its primary goal is to give users easy access to thousands of internet radio stations. The entire interface and all features have been designed with full accessibility for NVDA in mind.
FreeRadio គឺជាកម្មវិធីជំនួយវិទ្យុលើបណ្ដាញអ៊ីនធឺណិតសម្រាប់កម្មវិធីអានអេក្រង់ NVDA ។ គោលដៅចម្បងរបស់វាគឺដើម្បីផ្ដល់ឱ្យអ្នកប្រប្រាស់ចូលស្ដាប់វិទ្យុបានរហូតរាប់ពាន់ស្ថានីយ៉ាងងាយស្រួល។ ផ្ទៃកម្មវិធីទាំងមូល និងមុខងារទាំងអស់ ត្រូវបានរចនាឡើងដោយគិតគូរជាចម្បងពីភាពងាយស្រួលប្រើប្រាស់ទាំងស្រុងសម្រាប់ NVDA។

## Radio Browser Directory
ថតកម្មវិធីរុករកវិទ្យុ

FreeRadio uses the [Radio Browser](https://www.radio-browser.info/) open database for its station catalogue. Radio Browser is a community-managed, free directory hosting more than 50,000 internet radio stations from around the world. No registration or account is required and its API is open to everyone. Each station includes address, country, genre, language and bitrate information; stations are ranked by user votes. FreeRadio connects to this API through mirror servers located in Germany, the Netherlands and Austria; if one server is unreachable, it automatically switches to the next.
FreeRadio ប្រើ [Radio Browser](https://www.radio-browser.info/) បើកមូលដ្ឋានទិន្នន័យសម្រាប់កាតាឡុកស្ថានីយ៍របស់វា។ កម្មវិធីរុករកវិទ្យុគឺជាបញ្ជីរាយបញ្ជីឥតគិតថ្លៃដែលគ្រប់គ្រងដោយសហគមន៍ដែលមានស្ថានីយ៍វិទ្យុអ៊ីនធឺណិតជាង៥០០០០ មកពីជុំវិញពិភពលោក។ គ្មានការចុះឈ្មោះ ឬទាមទារគណនីនោះទេ ហើយ API របស់វាបើកចំហសម្រាប់មនុស្សគ្រប់គ្នា។ ស្ថានីយនីមួយៗរួមមានអាសយដ្ឋាន ប្រទេស ប្រភេទ ភាសា និងព័ត៌មានអត្រាប៊ីត។ ស្ថានីយ៍ត្រូវបានចាត់ថ្នាក់ដោយការបោះឆ្នោតរបស់អ្នកប្រើប្រាស់។ FreeRadio ភ្ជាប់ទៅ API នេះតាមរយៈម៉ាស៊ីនមេចម្លងដែលមានទីតាំងនៅប្រទេសអាល្លឺម៉ង់ ហូឡង់ និងអូទ្រីស។ ប្រសិនបើម៉ាស៊ីនមេមួយមិនអាចទៅដល់បានទេ វានឹងប្តូរទៅបន្ទាប់ដោយស្វ័យប្រវត្តិ។

## Adding a Station to Radio Browser
ការបន្ថែមស្ថានីយ៍ទៅកម្មវិធីរុករកវិទ្យុ

If a station you are looking for is not in the Radio Browser directory, you can submit it yourself at [https://www.radio-browser.info/add](https://www.radio-browser.info/add). No account or registration is needed.
ប្រសិនបើស្ថានីយ៍ដែលអ្នកកំពុងស្វែងរកមិនមាននៅក្នុងថតកម្មវិធីរុករកវិទ្យុ អ្នកអាចដាក់ស្នើវាដោយខ្លួនឯងតាមរយៈ [https://www.radio-browser.info/add](https://www.radio-browser.info/add)។ មិនចាំបាច់មានគណនី ឬចុះឈ្មោះទេ។

Fill in the form on that page:
បំពេញទម្រង់បែបបទនៅលើទំព័រនោះ:

- **Stream URL** *(required)* — the direct URL of the audio stream, ending in `.mp3`, `.aac`, `.ogg` or similar. This is not the station website address; it is the raw stream address you would paste into a media player. Most stations publish their stream URL on their website or in their "Listen live" section.
- **URL ស្ទ្រីម** (ចាំបាច់)* — ជាអាសយដ្ឋាន URL ផ្ទាល់នៃស្ទ្រីមសំឡេង ដែលបញ្ចប់ដោយ `.mp3`, `.aac`, `.ogg` ឬទម្រង់ស្រដៀងគ្នា។ នេះមិនមែនជាអាសយដ្ឋានគេហទំព័ររបស់ស្ថានីយ៍ឡើយ វាគឺជាអាសយដ្ឋានស្ទ្រីមផ្ទាល់ដែលអ្នកត្រូវយកទៅចម្លងដាក់ក្នុងកម្មវិធីចាក់មេឌៀ។ ស្ថានីយ៍ភាគច្រើនតែងតែដាក់បង្ហាញ URL ស្ទ្រីមរបស់ពួកគេនៅលើគេហទំព័រផ្ទាល់ ឬនៅក្នុងផ្នែក "ស្តាប់ផ្ទាល់"។
- **Station name** *(required)* — the name of the station as it should appear in the directory.
- **ឈ្មោះស្ថានីយ៍វិទ្យុ** *(ចាំបាច់)* — ឈ្មោះស្ថានីយ៍វិទ្យុដូចដែលមានបង្ហាញនៅក្នុងថត។
- **Homepage** — the station's website address.
- **ទំព័រដើម** — អាសយដ្ឋានគេហទំព័ររបស់ស្ថានីយ៍វិទ្យុ។
- **Country and language** — select the country and the broadcast language from the dropdown lists.
- **ប្រទេសនិងភាសា** — ជ្រើសរើសប្រទេស និងភាសាដែលផ្សាយចេញពីក្នុងបញ្ជីជម្រើស។
- **Tags** — genre or topic keywords separated by commas, for example `news`, `jazz`, `classical`. These are used for searching and filtering.
- **ស្លាក** — ពាក្យគន្លឹះសម្រាប់ប្រភេទ ឬប្រធានបទ ដែលបំបែកដោយសញ្ញាក្បៀស ឧទាហរណ៍ `news`, `jazz`, `classical`។ ពាក្យទាំងនេះត្រូវបានប្រើសម្រាប់ការស្វែងរក និងការសម្រាំងយក។
- **Logo URL** — a direct link to the station's logo image, if available.
- **ឡូហ្គោ URL** — តំណភ្ជាប់ផ្ទាល់ទៅកាន់រូបភាពឡូហ្គោរបស់ស្ថានីយ៍ ប្រសិនបើមាន។

After submitting, the station is reviewed and added to the public directory. Once accepted it will appear in FreeRadio's search and country listings automatically, since the directory is refreshed from the live API.
បន្ទាប់ពីដាក់ស្នើ ស្ថានីយវិទ្យុត្រូវបានពិនិត្យ និងបញ្ចូលក្នុងបញ្ជីសាធារណៈ។ នៅពេលទទួលយក វានឹងបង្ហាញនៅក្នុងការស្វែងរករបស់ FreeRadio និងបញ្ជីប្រទេសដោយស្វ័យប្រវត្តិ ចាប់តាំងពីថតត្រូវបានផ្ទុកឡើងវិញពី API ផ្ទាល់។

## Requirements
## តម្រូវការ

- NVDA 2024.1 or later
- NVDA 2024.1 ឬក្រោយនេះ
- Windows 10 or later
- Windows 10 ឬថ្មីជាងនេះ
- Internet connection
- ការតភ្ជាប់អ៊ីនធឺណិត

## Installation
## ការដំឡើង

Download the `.nvda-addon` file, press Enter on it and restart NVDA when prompted.
ទាញយកឯកសារ `.nvda-addon` ចុច Enter នៅលើវា ហើយចាប់ផ្តើម NVDA ឡើងវិញ នៅពេលត្រូវបានសួរ។

## Keyboard Shortcuts
## គ្រាប់ចុចរហ័ស

All shortcuts can be reassigned from NVDA Menu → Preferences → Input Gestures → FreeRadio. These shortcuts work from anywhere, regardless of which window has focus.
គ្រាប់ចុចរហ័សទាំងអស់អាចត្រូវបានកំណត់ឡើងវិញពីក្នុងម៉ឺនុយរបស់ NVDA → ចំណូលចិត្ត → ចលនាថ្នាក់បញ្ចូល → FreeRadio. គ្រាប់ចុចរហ័សទាំងនេះអាចប្រើប្រាស់បានពីគ្រប់ទីកន្លែង ដោយមិនគិតថាវីនដូណាមួយកំពុងសកម្មនោះឡើយ។

| Shortcut | Function | Description |
| គ្រាប់ចុចរហ័ស | មុខងារ | ការពិពណ៌នា |
|---|---|---|
| `Ctrl+Win+R` | Open station browser | Opens the browser window if closed, or brings it to the foreground if already open. |
| `Ctrl+Win+R` | បើកកម្មវិធីរុករកស្ថានីវិទ្យុតាមអ៊ីនធឺណិត | បើកកម្មវិធីរុករករបស់វីនដូប្រសិនបើបិទ ឬនាំវាទៅផ្ទៃខាងមុខប្រសិនបើបើករួចហើយ។ |
| `Ctrl+Win+P` | Pause / resume | Pauses the current station if playing; resumes if paused. If nothing is playing, starts the last station or opens the favourites list depending on your setting. Pressing twice in quick succession jumps directly to a tab of your choice. Pressing three times can trigger a separate action depending on your setting. |
| `Ctrl+Win+P` | ផ្អាក ឬបន្ត | ផ្អាកស្ថានីយវិទ្យុបច្ចុប្បន្នប្រសិនបើកំពុងចាក់ ហើយបន្តប្រសិនបើផ្អាក។ ប្រសិនបើគ្មានអ្វីកំពុងចាក់ទេនោះ ចាប់ផ្តើមស្ថានីយវិទ្យុដែលចាក់ក្រោយគេ ឬបើកបញ្ជីចំណូលចិត្ត អាស្រ័យលើការកំណត់របស់អ្នក។ ចុចពីរដងជាប់ៗគ្នារហ័សលោតដោយផ្ទាល់ទៅផ្ទាំងដែលអ្នកជ្រើសរើស។ ចុចបីដងអាចបង្កឱ្យមានសកម្មភាពដាច់ដោយឡែក អាស្រ័យលើការកំណត់របស់អ្នក។ |
| `Ctrl+Win+S` | Stop | Fully stops the current station and resets the player. |
| `Ctrl+Win+S` | បញ្ឈប់ | បញ្ឈប់ទាំងស្រុងនូវការចាក់ស្ថានីយវិទ្យុបច្ចុប្បន្ន ហើយកំណត់កម្មវិធីចាក់ឡើងវិញ។ |
| `Ctrl+Win+→` | Next favourite | Moves to the next station in the favourites list. Wraps around to the beginning at the end of the list. |
| `Ctrl+Win+→` | ចំណូលចិត្តបន្ទាប់ | ផ្លាស់ទីទៅស្ថានីយវិទ្យុបន្ទាប់ក្នុងបញ្ជីចំណូលចិត្ត។ វិលត្រឡប់ទៅចំណុចចាប់ផ្ដើមវិញ នៅពេលដល់ចុងបញ្ចប់នៃបញ្ជី។ |
| `Ctrl+Win+←` | Previous favourite | Moves to the previous station in the favourites list. Jumps to the end when at the beginning. |
| `Ctrl+Win+←` | ចំណូលចិត្តមុន | ផ្លាស់ទីទៅស្ថានីយវិទ្យុមុនក្នុងបញ្ជីចំណូលចិត្ត។ លោតទៅចុងបញ្ចប់នៅពេលស្ថិតក្នុងចំណុចចាប់ផ្តើម។ |
| `Ctrl+Win+↑` | Volume up | Increases volume by 10; maximum 100. |
| `Ctrl+Win+↑` | បង្កើនកម្រិតសំឡេង | ដំឡើងសំឡេងម្ដង១០ លេខ ដែលកម្រិតខ្ពស់បំផុតត្រឹម១០០។ |
| `Ctrl+Win+↓` | Volume down | Decreases volume by 10; minimum 0. |
| `Ctrl+Win+↑` | បន្ថយកម្រិតសំឡេង | បន្ថយសំឡេងម្ដង១០ លេខ ដែលកម្រិតទាបបំផុតត្រឹម០។ |
| `Ctrl+Win+V` | Add to favourites | Adds the currently playing station to the favourites list. Announces if the station is already in the list. |
| `Ctrl+Win+V` | បន្ថែមទៅក្នុងចំណូលចិត្ត | បន្ថែមស្ថានីយ៍វិទ្យុដែលកំពុងចាក់បច្ចុប្បន្នទៅក្នុងបញ្ជីដែលចូលចិត្ត។ ប្រាប់ព័ត៌មានប្រសិនបើស្ថានីយមាននៅក្នុងបញ្ជីរួចហើយ។ |
| `Ctrl+Win+I` | Station info | Announces the currently playing station name. Press twice to show details such as country, genre and bitrate in a dialog. Press three times to copy the current track info (ICY metadata) to the clipboard if available; if no metadata is present, starts Shazam music recognition instead. Press four times to force music recognition in case of wrong ICY metadata. |
| `Ctrl+Win+I` | ព័ត៌មានស្ថានីយ៍វិទ្យុ | ប្រាប់ឈ្មោះស្ថានីយ៍វិទ្យុដែលកំពុងចាក់។ ចុចពីរដងដើម្បីបង្ហាញព័ត៌មានលម្អិតដូចជា ប្រទេស ប្រភេទ និងអត្រាប៊ីតនៅក្នុងប្រអប់។ ចុចបីដងដើម្បីចម្លងព័ត៌មានបទចម្រៀង ឬតន្ត្រីបច្ចុប្បន្ន (ទិន្នន័យមេតា ICY) ទៅកាន់ clipboard ប្រសិនបើមាន ប្រសិនបើគ្មានទិន្នន័យមេតាមានវត្តមាន វានឹងចាប់ផ្តើមការស្វែងរកបទចម្រៀង ឬតន្ត្រីតាម Shazam ជំនួសវិញ។ ចុចបួនដង ដើម្បីបញ្ជាឱ្យស្វែងរកបទចម្រៀង ឬតន្ត្រីដែលមិនស្គាល់ចំណងជើង ក្នុងករណីដែលទិន្នន័យមេតា ICY មិនត្រឹមត្រូវ។ |
| `Ctrl+Win+M` | Audio mirror | Mirrors the current stream to an additional audio output device simultaneously. Press again to stop mirroring. |
| `Ctrl+Win+M` | ចម្លងសំឡេង | ចម្លងសំឡេងផ្សាយបច្ចុប្បន្នទៅឧបករណ៍បញ្ចេញសំឡេងបន្ថែមក្នុងពេលដំណាលគ្នា។ ចុចម្តងទៀតដើម្បីបញ្ឈប់ការចម្លង។ |
| `Ctrl+Win+E` | Instant recording | Press once to start recording the current station; press again to stop. Press **twice** to start a **song recording** — the file is named after the current track and the recording stops automatically when the track changes. Press twice again while a song recording is active to stop it early. Playback continues uninterrupted in all recording modes. Only available for stations that broadcast ICY metadata. |
| `Ctrl+Win+E` | ការថតភ្លាមៗ | ចុចម្តងដើម្បីចាប់ផ្តើមថតស្ថានីយ៍វិទ្យុបច្ចុប្បន្ន ហើយចុចម្តងទៀតដើម្បីបញ្ឈប់។ ចុច **ពីរដង** ដើម្បីចាប់ផ្តើម **ការថតបទចម្រៀង** — ឯកសារត្រូវបានដាក់ឈ្មោះតាមបទចម្រៀង ឬតន្ត្រីបច្ចុប្បន្ន ហើយការថតនឹងឈប់ដោយស្វ័យប្រវត្តិពេលបចម្រៀង ឬតន្ត្រីទផ្លាស់ប្តូរ។ ចុចពីរដងម្តងទៀត ក្នុងពេលការថតបទចម្រៀងកំពុងដំណើរការ ដើម្បីបញ្ឈប់វាទាន់ពេល។ ការចាក់នឹងបន្តដោយមិនមានការរំខាននៅក្នុងម៉ូដថតទាំងអស់។ មានសម្រាប់តែស្ថានីយដែលផ្សាយទិន្នន័យមេតា ICY ប៉ុណ្ណោះ។ |
| `Ctrl+Win+W` | Open recordings folder | Opens the folder containing recorded files in File Explorer. |
| `Ctrl+Win+W` | បើកថតឯកសារ | បើកថតដែលមានឯកសារដែលបានថតទុកនៅក្នុង File Explorer។ |
| *(unassigned)* | Toggle mute notifications | Toggles the Mute Notifications setting on the fly. Assign a key combination via NVDA Menu → Preferences → Input Gestures → FreeRadio. |
| *(មិនបានកំណត់គ្រាប់ចុច)* | បិទ ឬបើកការផ្អាកសំឡេងជូនដំណឹង | បិទ ឬបើកការកំណត់នៃការផ្អាកសំឡេងជូនដំណឹងភ្លាមៗ។ សូមចូលទៅកំណត់គ្រាប់ចុចផ្សំតាមរយៈម៉ឺនុយរបស់ NVDA → ចំណូលចិត្ត → ចលនាថ្នាក់បញ្ចូល → FreeRadio. |

Next / previous shortcuts only navigate the favourites list; they do not work with the all stations list. When a list is focused in the browser window, the left and right arrow keys serve the same purpose — see In-Dialog Shortcuts.
គ្រាប់ចុចរហ័សបន្ទាប់ / មុនគ្រាន់តែរុករកបញ្ជីចំណូលចិត្តប៉ុណ្ណោះ គឺវាមិនដំណើរការជាមួយបញ្ជីស្ថានីយ៍វិទ្យុទាំងអស់នោះទេ។ នៅពេលដែលបញ្ជីមួយត្រូវបានផ្ដោតនៅក្នុងកម្មវិធីរុករកតាមអ៊ីនធឺណិតរបស់វីនដូ គ្រាប់ចុចព្រួញខាងឆ្វេង និងខាងស្តាំបម្រើគោលបំណងដូចគ្នា — សូមមើលក្នុងប្រអប់គ្រាប់ចុចរហ័ស។

## Station Browser
## កម្មវិធីរុករកស្ថានីយ៍វិទ្យុ

FreeRadio also adds a **FreeRadio** submenu to the NVDA Tools menu. From there you can directly open the Station Browser and FreeRadio Settings.
FreeRadio ក៏បន្ថែមម៉ឺនុយរង **FreeRadio** ទៅម៉ឺនុយឧបករណ៍ NVDA ផងដែរ។ នៅក្នុងទីនោះអ្នកអាចបើកកម្មវិធីរុករកស្ថានីយ៍វិទ្យុ និងការកំណត់ FreeRadio ដោយផ្ទាល់។

The window opened with `Ctrl+Win+R` contains five tabs: All Stations, Favourites, Recording, Timer, and Liked Songs. You can navigate between tabs with `Ctrl+Tab`.
វីនដូដែលបើកដោយប្រើ `Ctrl+Win+R` មានប្រាំផ្ទាំង: ស្ថានីយ៍វិទ្យុទាំងអស់ ចំណូលចិត្ត ឯកសារថត កម្មវិធីកំណត់ម៉ោង និងចម្រៀងដែលចូលចិត្ត។ អ្នកអាចរុករករវាងផ្ទាំងទាំងនោះដោយប្រើ `Ctrl+Tab`.

When the All Stations tab opens, the top 1,000 most-voted stations are automatically loaded from Radio Browser. Selecting a country from the dropdown updates the list to show that country's stations. Typing in the search field instantly  performs a full search across the entire Radio Browser database simultaneously by name, country and genre.
នៅពេលផ្ទាំងស្ថានីយ៍វិទ្យុទាំងអស់បើក ស្ថានីយ៍ដែលមានការបោះឆ្នោតច្រើនជាងគេបំផុតចំនួន១០០០ ត្រូវបានដំណើរការដោយស្វ័យប្រវត្តិពីកម្មវិធីរុករកវិទ្យុ។ ការជ្រើសរើសប្រទេសមួយពីបញ្ជីជម្រើស គឺធ្វើបច្ចុប្បន្នភាពបញ្ជីដើម្បីបង្ហាញស្ថានីយវិទ្យុរបស់ប្រទេសនោះ។ ការវាយបញ្ចូលក្នុងកន្លែងស្វែងរកភ្លាមៗ ធ្វើការស្វែងរកពេញទូទាំងមូលដ្ឋានទិន្នន័យកម្មវិធីរុករកវិទ្យុទាំងមូលក្នុងពេលដំណាលគ្នាតាមឈ្មោះ ប្រទេស និងប្រភេទ។

The **Output Device** dropdown at the bottom of the browser window — outside the tabs — lists all BASS-recognised audio output devices. Selecting a device immediately redirects audio output to it and saves the choice permanently; the same device is used automatically in the next session. If the selected device is not connected, the add-on falls back to the system default automatically. This control is only functional when the BASS backend is active.
ប្រអប់ជម្រើស **ឧបករណ៍បញ្ចេញសំឡេង** នៅផ្នែកខាងក្រោមនៃវីនដូកម្មវិធីរុករក — នៅខាងក្រៅផ្ទាំងផ្សេងៗ — រាយបញ្ជីឧបករណ៍បញ្ចេញសំឡេងដែលទទួលស្គាល់ដោយ BASS ទាំងអស់។ ការជ្រើសរើសឧបករណ៍ភ្លាមៗប្តូរទិសលទ្ធផលសំឡេងទៅឧបករណ៍នោះ ហើយរក្សាទុកជម្រើសជាអចិន្ត្រៃយ៍ ចំណែកឧបករណ៍ដូចគ្នានេះត្រូវបានប្រើដោយស្វ័យប្រវត្តិនៅក្នុងផ្នែកបន្ទាប់។ ប្រសិនបើឧបករណ៍ដែលបានជ្រើសរើសមិនត្រូវបានភ្ជាប់ កម្មវិធីជំនួយនឹងត្រលប់ទៅប្រព័ន្ធលំនាំដើមដោយស្វ័យប្រវត្តិ។ ការគ្រប់គ្រងនេះមានមុខងារតែនៅពេលដែលកម្មវិធីខាងក្រោយ BASS ដំណើរការប៉ុណ្ណោះ។

The **Volume** (0–200) and **Effects** controls in the same area can be adjusted at any time while the window is open. From the Effects list, Chorus, Compressor, Distortion, Echo, Flanger, Gargle, Reverb, EQ: Bass Boost, EQ: Treble Boost and EQ: Vocal Boost can be enabled simultaneously; changes are applied to the active stream instantly. These controls are fully functional only when the BASS backend is active.
**កម្រិតសំឡេង** (0–200) និង **បែបផែនសំឡេង** គ្រប់គ្រងក្នុងកន្លែងដូចគ្នា អាចនឹងត្រូវបានកែតម្រូវគ្រប់ពេលវេលានៅពេលដែលវីនដូបើក។ ពីក្នុងបញ្ជីបែបផែនសំឡេងរួមមាន Chorus, Compressor, Distortion, Echo, Flanger, Gargle, Reverb, EQ: Bass Boost, EQ: Treble Boost និង EQ: Vocal Boost អាចនឹងត្រូវបានបើកក្នុងពេលដំណាលគ្នា រីឯការផ្លាស់ប្តូរត្រូវបានអនុវត្តចំពោះដំណើរការផ្សាយភ្លាមៗ។ ការគ្រប់គ្រងទាំងនេះមានមុខងារពេញលេញតែនៅពេលដែលកម្មវិធីខាងក្រោយ BASS ដំណើរការប៉ុណ្ណោះ។

The **Play/Pause** button is also located at the bottom of the window. If no station is playing it starts the selected station; if a station is already playing it pauses playback.
ប៊ូតុង **ចាក់ ឬផ្អាក** ក៏មានទីតាំងនៅខាងក្រោមវីនដូផងដែរ។ ប្រសិនបើគ្មានស្ថានីយ៍វិទ្យុកំពុងចាក់ទេ វាចាប់ផ្តើមស្ថានីយវិទ្យុដែលបានជ្រើសរើស ប្រសិនបើស្ថានីយ៍វិទ្យុកំពុងចាក់រួចហើយ វាផ្អាកការចាក់នោះ។

When a station is selected in the list, the **Station Details** button displays information such as country, language, genre, format, bitrate, website and stream URL in a separate dialog. Each field appears in its own read-only text box; you can move between fields with Tab and copy all information to the clipboard at once with the **Copy all to clipboard** button. This button is available in both the All Stations and Favourites tabs.
នៅពេលដែលស្ថានីយ៍វិទ្យុត្រូវបានជ្រើសរើសនៅក្នុងបញ្ជី ប៊ូតុង **ព័ត៌មានលម្អិតអំពីស្ថានីយ៍វិទ្យុ** បង្ហាញព័ត៌មានដូចជាប្រទេស ភាសា ប្រភេទ ទ្រង់ទ្រាយ អត្រាប៊ីត គេហទំព័រ និង URL ផ្សាយក្នុងប្រអប់ដាច់ដោយឡែកមួយ។ កន្លែងនីមួយៗមានបង្ហាញនៅក្នុងប្រអប់អត្ថបទត្រឹមតែសម្រាប់អានផ្ទាល់របស់វា អ្នកអាចផ្លាស់ទីតាមវាលដោយប្រើថេប ហើយចម្លងព័ត៌មានទាំងអស់ទៅកាន់ clipboard ក្នុងពេលតែមួយដោយប្រើប៊ូតុង **ចម្លងទាំងអស់ទៅកាន់ clipboard**។ ប៊ូតុងនេះមានទាំងនៅក្នុងស្ថានីយវិទ្យុទាំងអស់ និងផ្ទាំងចំណូលចិត្ត។

### In-Dialog Shortcuts
### គ្រាប់ចុចរហ័សក្នុងប្រអប់

The following keys work only while the Station Browser window is active.
គ្រាប់ចុចខាងក្រោមដំណើរការតែនៅក្នុងពេលដែលវីនដូកម្មវិធីរុករកស្ថានីយ៍ដំណើរការប៉ុណ្ណោះ។

### F Keys
### គ្រាប់ចុច F

| Shortcut | Function | Description |
| គ្រាប់ចុចរហ័ស | មុខងារ | ការពិពណ៌នា |
|---|---|---|
| `F1` | Help guide | Opens the add-on's help file in the default browser. The guide for the active NVDA language is searched first; if not found, the default guide is opened. |
| `F1` | ជំនួយណែនាំ | បើកឯកសារជំនួយរបស់កម្មវិធីជំនួយនៅក្នុងកម្មវិធីរុករកលំនាំដើម។ ការណែនាំសម្រាប់ភាសា NVDA ដែលមានត្រូវបានស្វែងរកជាមុន ហើយប្រសិនបើរកមិនឃើញ ការណែនាំលំនាំដើមត្រូវបានបើក។ |
| `F2` | what's playing | Announces the currently playing station and track name. Press twice to show details such as country, genre and bitrate in a dialog. Press three times to copy the current track info (ICY metadata) to the clipboard if available; if no metadata is present, starts Shazam music recognition instead. Press four times to force music recognition in case of wrong ICY metadata. |
| `F2` | អ្វីៗដែលកំពុងចាក់ | ប្រកាសឈ្មោះស្ថានីយ៍វិទ្យុ និងបចម្រៀង ឬតន្ត្រីដែលកំពុងចាក់។ ចុចពីរដងដើម្បីបង្ហាញព័ត៌មានលម្អិតដូចជាប្រទេស ប្រភេទ និងអត្រាប៊ីតនៅក្នុងប្រអប់។ ចុចបីដងដើម្បីចម្លងព័ត៌មានបទចម្រៀង ឬតន្ត្រីបច្ចុប្បន្ន (ទិន្នន័យមេតា ICY) ទៅកាន់ clipboard ប្រសិនបើមាន ហើយប្រសិនបើមិនមានទិន្នន័យមេតាទេ ចាប់ផ្តើមការស្វែងរកបទចម្រៀង ឬតន្ត្រីដែលមិនស្គាល់ចំណងជើងដោយប្រើ Shazam ជំនួសវិញ។ ចុចបួនដងដើម្បីបញ្ជាឱ្យមានការស្វែងរកបទចម្រៀង ឬតន្ត្រីដែលមិនស្គាល់ចំណងជើងក្នុងករណីមានទិន្នន័យមេតា ICY ខុស។ |
| `F3` | Previous station | Moves to the previous station in the All Stations or Favourites tab and starts playing immediately. Jumps to the end when at the beginning of the list. |
| `F3` | ស្ថានីយ៍វិទ្យុមុន | ផ្លាស់ទីទៅស្ថានីយវិទ្យុមុននៅក្នុងផ្ទាំង ស្ថានីយ៍ទាំងអស់ ឬចំណូលចិត្ត ហើយចាប់ផ្តើមចាក់ភ្លាមៗ។ លោតទៅចុងបញ្ចប់នៅពេលដែលវាស្ថិតនៅដើមបញ្ជី។ |
| `F4` | Next station | Moves to the next station in the All Stations or Favourites tab and starts playing immediately. Wraps to the beginning at the end of the list. |
| `F4` | ស្ថានីយ៍វិទ្យុបន្ទាប់ | ផ្លាស់ទីទៅស្ថានីយបន្ទាប់នៅក្នុងផ្ទាំង ស្ថានីយ៍ទាំងអស់ ឬចំណូលចិត្ត ហើយចាប់ផ្តើមចាក់ភ្លាមៗ។ ត្រឡប់ទៅផ្នែកខាងដើមពេលស្ថិតនៅចុងបញ្ចប់នៃបញ្ជី។ |
| `F5` | Volume down | Decreases volume by 10 (minimum 0). |
| `F5` | បន្ថយកម្រិតសំឡេង | បន្ថយសំឡេងម្ដង១០ លេខ (កម្រិតទាបបំផុតត្រឹម០)។ |
| `F6` | Volume up | Increases volume by 10 (maximum 200). |
| `F6` | ដំឡើងកម្រិតសំឡេង | ដំឡើងសំឡេងម្ដង១០ លេខ (កម្រិតខ្ពស់បំផុតត្រឹម១០០)។ |
| `F7` | Pause / resume | Pauses if a station is playing; resumes if paused and media is loaded. |
| `F7` | ផ្អាក ឬបន្ត | ផ្អាកសំឡេងប្រសិនបើស្ថានីយ៍វិទ្យុកំពុងចាក់ បន្តសំឡេងប្រសិនបើផ្អាក ហើយមេឌៀបានដំណើរការរួចរាល់។ |
| `F8` | Stop | Fully stops the current station and resets the player. |
| `F8` | បញ្ឈប់ | បញ្ឈប់សំឡេងទាំងស្រុងនូវស្ថានីយវិទ្យុបច្ចុប្បន្ន ហើយកំណត់កម្មវិធីចាក់ឡើងវិញ។ |
| `F9` | Rename | Opens rename dialog for focused station in favorits tab. |
| `F9` | ប្តូរឈ្មោះ | បើកប្រអប់ប្តូរឈ្មោះសម្រាប់ស្ថានីយ៍វិទ្យុដែលកំពុងផ្តោតនៅក្នុងផ្ទាំងចំណូលចិត្ត។ |

### List and Navigation Shortcuts
### បញ្ជី និងគ្រាប់ចុចរហ័សសម្រាប់ការរុករក

| Shortcut | Function | Description |
| គ្រាប់ចុចរហ័ស | មុខងារ | ការពិពណ៌នា |
|---|---|---|
| `→` | Next station | When the All Stations or Favourites list is focused, moves to the next station and plays it immediately. Wraps to the beginning at the end of the list. |
| `→` | ស្ថានីយ៍វិទ្យុបន្ទាប់ | នៅពេលដែលបញ្ជីស្ថានីយ៍វិទ្យុទាំងអស់ ឬចំណូលចិត្តត្រូវបានផ្តោត គឺនឹងផ្លាស់ទីទៅស្ថានីយវិទ្យុបន្ទាប់ ហើយចាក់វាភ្លាមៗ។ វិលត្រឡបទៅផ្នែកខាងដើមនៅចុងបញ្ចប់នៃបញ្ជី។ |
| `←` | Previous station | When the All Stations or Favourites list is focused, moves to the previous station and plays it immediately. Jumps to the end when at the beginning. |
| `←` | ស្ថានីយ៍វិទ្យុមុន | នៅពេលដែលបញ្ជីស្ថានីយ៍វិទ្យុទាំងអស់ ឬចំណូលចិត្តត្រូវបានផ្តោត គឺនឹងផ្លាស់ទីទៅស្ថានីយវិទ្យុមុន ហើយចាក់វាភ្លាមៗ។ លោតទៅចុងបញ្ចប់នៅចំណុចចាប់ផ្តើម។ |
| `Enter` | Play | When the All Stations or Favourites list is focused, starts playing the selected station immediately. Switches to the selected station even if another station is already playing. |
| `បញ្ចូល` | ចាក់សំឡេង | នៅពេលដែលបញ្ជីស្ថានីយ៍វិទ្យុទាំងអស់ ឬចំណូលចិត្តត្រូវបានផ្តោត គឺនឹងចាប់ផ្តើមចាក់ស្ថានីយវិទ្យុដែលបានជ្រើសរើសភ្លាមៗ។ ប្តូរទៅស្ថានីយ៍វិទ្យុដែលបានជ្រើសរើស ទោះបីជាស្ថានីយ៍វិទ្យុផ្សេងទៀតកំពុងចាក់រួចហើយក៏ដោយ។ |
| `Space` | Play / Pause | Pauses if a station is playing; otherwise starts playing the selected station. |
| `ដកឃ្លា` | ចាក់ ឬផ្អាក | ផ្អាកសំឡេងប្រសិនបើស្ថានីយ៍កំពុងចាក់ ឬបើមិនអ៊ីចឹង គឺនឹងចាប់ផ្តើមចាក់ស្ថានីយដែលបានជ្រើសរើស។ |
| `Ctrl+Tab` | Next tab | Switches to the next tab (All Stations → Favourites → Recording → Timer → Liked Songs). |
| `Ctrl+Tab` | ផ្ទាំងបន្ទាប់ | ប្តូរទៅផ្ទាំងបន្ទាប់ (ស្ថានីយ៍វិទ្យុទាំងអស់ → ចំណូលចិត្ត → សំឡេងថត → កម្មវិធីកំណត់ម៉ោង → ចម្រៀងដែលចូលចិត្ត)។ |
| `Ctrl+Shift+Tab` | Previous tab | Switches to the previous tab. |
| `Ctrl+Shift+Tab` | ផ្ទាំងមុន | ប្តូរទៅផ្ទាំងមុន។ |
| `Escape` | Hide | Hides the window; the add-on continues playing in the background. |
| `Escape` | លាក់ផ្ទៃវីនដូ | លាក់មិនឱ្យឃើញផ្ទៃវីនដូរបស់កម្មវិធី ចំណែកកម្មវិធីជំនួយនៅបន្តចាក់សំឡេងពីផ្ទៃខាងក្រោយដូចធម្មតា។ |

### Volume Shortcuts
### គ្រាប់ចុចរហ័សសម្រាប់កម្រិតសំឡេង

| Shortcut | Function | Description |
| គ្រាប់ចុចរហ័ស | មុខងារ | ការពិពណ៌នា |
|---|---|---|
| `Ctrl+↑` | Volume up | Increases volume by 10. Only works while the browser window is open. |
| `Ctrl+↑` | ដំឡើងកម្រិតសំឡេង | ដំឡើងកម្រិតសំឡេងម្ដង១០ លេខ។ ដំណើរការតែនៅពេលដែលវីនដូកម្មវិធីរុករកបើកប៉ុណ្ណោះ។ |
| `Ctrl+↓` | Volume down | Decreases volume by 10. Only works while the browser window is open. |
| `Ctrl+↓` | បន្ថយកម្រិតសំឡេង | បន្ថយកម្រិតសំឡេងម្ដង១០ លេខ។ ដំណើរការតែនៅពេលដែលវីនដូកម្មវិធីរុករកបើកប៉ុណ្ណោះ។ |

### Alt Key Shortcuts
### គ្រាប់ចុចរហ័សជាមួយ Alt

| Shortcut | Function | Description |
| គ្រាប់ចុចរហ័ស | មុខងារ | ការពិពណ៌នា |
|---|---|---|
| `Alt+R` | Go to search field | Moves focus to the search text box. Searches Radio Browser with the text in the search field; name, country and genre are searched simultaneously. |
| `Alt+R` | ទៅកាន់កន្លែងស្វែងរក| ផ្លាស់ទីទៅប្រអប់ស្វែងរកអត្ថបទ។ ស្វែងរកកម្មវិធីរុករកវិទ្យុជាមួយនឹងអត្ថបទនៅក្នុងកន្លែងស្វែងរក ចំណែកឯឈ្មោះ ប្រទេស និងប្រភេទត្រូវបានស្វែងរកក្នុងពេលដំណាលគ្នា។ |
| `Alt+V` | Add / remove favourite | Adds the selected station to favourites; removes it if already in the list. |
| `Alt+V` | បន្ថែម ឬលុបចំណូលចិត្ត | បន្ថែមស្ថានីយវិទ្យុដែលបានជ្រើសរើសទៅក្នុងចំណូលចិត្ត ហើយលុបវាចេញប្រសិនបើមាននៅក្នុងបញ្ជី។ |
| `Alt+1` | All Stations | Switches to the All Stations tab. |
| `Alt+1` | ស្ថានីយ៍វិទ្យុទាំងអស់ | ប្តូរទៅផ្ទាំងស្ថានីយ៍វិទ្យុទាំងអស់។ |
| `Alt+2` | Favourites | Switches to the Favourites tab. |
| `Alt+2` | ចំណូលចិត្ត | ប្តូរទៅផ្ទាំងចំណូលចិត្ត។ |
| `Alt+3` | Recording | Switches to the Recording tab. |
| `Alt+3` | សំឡេងថត | ប្តូរទៅផ្ទាំងសំឡេងថត។ |
| `Alt+4` | Timer | Switches to the Timer tab. |
| `Alt+4` | កម្មវិធីកំណត់ម៉ោង | ប្តូរទៅផ្ទាំងកម្មវិធីកំណត់ម៉ោង។ |
| `Alt+5` | Liked Songs | Switches to the Liked Songs tab. |
| `Alt+5` | ចម្រៀងដែលចូលចិត្ត | ប្តូរទៅផ្ទាំងចម្រៀងដែលចូលចិត្ត។ |
| `Alt+K` | Close | Closes the window; the add-on continues playing in the background. |
| `Alt+K` | បិទ | បិទផ្ទៃវីនដូ រីឯកម្មវិធីជំនួយបន្តចាក់សំឡេងនៅផ្ទៃខាងក្រោយ។ |

## Favourites
## ចំណូលចិត្ត

The favourites list is a personal station collection stored permanently. To add a station, select it in the list and press the Add to Favourites button or use the `Alt+V` shortcut. The same shortcut removes a station that is already in the list when it is selected.
បញ្ជីចំណូលចិត្តគឺជាការប្រមូលស្ថានីយ៍វិទ្យុផ្ទាល់ខ្លួនដែលរក្សាទុកជាអចិន្ត្រៃយ៍។ ដើ្ម្បីបន្ថែមស្ថានីវិទ្យុមួយបាន សូមជ្រើសរើសវានៅក្នុងបញ្ជី រួចចុចប៊ូតុងបន្ថែមទៅក្នុងចំណូលចិត្ត ឬមួយអាចប្រើគ្រាប់ចុចរហ័ស `Alt+V`។ គ្រាប់ចុចរហ័សដូចគ្នានេះ នឹងលុបស្ថានីវិទ្យុដែលមាននៅក្នុងបញ្ជីរួចហើយ នៅពេលដែលវាត្រូវបានជ្រើសរើស។

Favourites can be played with `Ctrl+Win+→` and `Ctrl+Win+←`; these shortcuts work even when the browser window is not open.
ចំណូលចិត្តអាចត្រូវបានចាក់សំឡេងដោយប្រើ `Ctrl+Win+→` និង `Ctrl+Win+←` ហើយគ្រាប់ចុចរហ័សទាំងនេះអាចប្រើការបាន បើទោះជាវីនដូរុករកកម្មវិធីមិនបានបើកក៏ដោយ។

To delete a station from the favourites list, select it and press the **Delete Station** button or the `Delete` key. After deletion, focus and selection automatically move to the next station in the list. If the deleted station was the last one, focus moves to the previous station. If the list becomes empty, focus moves to the Play button.
ដើម្បីលុបស្ថានីវិទ្យុមួយចេញពីបញ្ជីចំណូលចិត្ត ត្រូវជ្រើសរើសយកវា រួចសូមចុចប៊ូតុង **លុបStation** ឬមួយក៏គ្រាប់ចុច `លុប`។ ក្រោយពីការលុបនេះ ទ្រនិចផ្ដោត និងការជ្រើសរើសនឹងផ្លាស់ទីទៅស្ថានីវិទ្យុនៅក្នុងបញ្ជី។ ប្រសិនបើស្ថានីយវិទ្យុដែលបានលុបគឺជាស្ថានីយចុងក្រោយ ទ្រនិចផ្ដោតនឹងផ្លាស់ទីទៅស្ថានីវិទ្យុមុន។ ប្រសិនបើបញ្ជីទទេ ទ្រនិចផ្ដោតនឹងផ្លាស់ទីទៅប៊ូតុងចាក់សំឡេង។

### Reordering Favourites
### ការតម្រៀបចំណូលចិត្តឡើងវិញ

With a station selected in the Favourites tab, press `comma` to enter move mode — you will hear a beep. Navigate to the target position with the arrow keys, then press `comma` again. The station is placed at the chosen position and the new order is saved immediately. Pressing `comma` again at the same position cancels the move.
ជាមួយនឹងស្ថានីយ៍វិទ្យុដែលបានជ្រើសរើសនៅក្នុងផ្ទាំងចំណូលចិត្ត សូមចុច `comma` ដើម្បីចូលទៅក្នុងម៉ូដផ្លាស់ទី — អ្នកនឹងឮសំឡេងប៊ីប។ រុករកទៅទីតាំងគោលដៅដោយប្រើគ្រាប់ចុចព្រួញ រួចសូមចុច `comma` ម្តងទៀត។ ស្ថានីយ៍វិទ្យុនឹងត្រូវបានដាក់នៅទីតាំងដែលបានជ្រើសរើស ហើយលំដាប់លំដោយថ្មីត្រូវបានរក្សាទុកភ្លាមៗ។ ចុច `comma` ម្តងទៀតនៅទីតាំងដដែលដើ្បីលុបចោលការផ្លាស់ទី។

### Adding a Custom Station
### ការបន្ថែមស្ថានីយ៍ផ្ទាល់ខ្លួន

To add a station that is not in Radio Browser, use the Add Custom Station button. In the dialog that appears, enter the station name and stream URL to add it directly to your favourites. Custom stations can be played and reordered just like any other favourite.
ដើម្បីបន្ថែមស្ថានីយ៍វិទ្យុដែលមិនមាននៅក្នុងកម្មវិធីរុករកវិទ្យុ សូមប្រើប៊ូតុងបន្ថែមស្ថានីយ៍ផ្ទាល់ខ្លួន។ នៅក្នុងប្រអប់ដែលលេចឡើង សូមបញ្ចូលឈ្មោះស្ថានីយ៍ និង URL ស្ទ្រីមដើម្បីបន្ថែមវាដោយផ្ទាល់ទៅចំណូលចិត្តរបស់អ្នក។ ស្ថានីយ៍ផ្ទាល់ខ្លួនអាចចាក់សំឡេង និងរៀបចំលំដាប់លំដោយឡើងវិញបានដូចអ្វីដែលចូលចិត្តផ្សេងទៀតដែរ។

### Station Audio Profile
### ទម្រង់សំឡេងរបស់ស្ថានីវិទ្យុ

The Favourites tab includes two buttons for managing per-station audio settings:
ផ្ទាំងចំណូលចិត្តរួមមានប៊ូតុងពីរសម្រាប់គ្រប់គ្រងការកំណត់សំឡេងក្នុងមួយស្ថានីយវិទ្យុ:

**Save Audio Profile for This Station** — saves the current volume level and active effects (chorus, EQ, etc.) as a profile tied to that specific station. Whenever that station starts playing, its saved volume and effects are automatically applied, overriding the global defaults.
**រក្សាទុកទម្រង់សំឡេងសម្រាប់ស្ថានីយ៍នេះ** — រក្សាទុកកម្រិតសំឡេងបច្ចុប្បន្ន និងបែបផែនសំេងសកម្ម (chorus, EQ, etc.) ជាទម្រង់ភ្ជាប់ទៅស្ថានីយវិទ្យុជាក់លាក់នោះ។ នៅពេលណាដែលស្ថានីយវិទ្យុនោះចាប់ផ្តើមចាក់សំឡេង កម្រិតសំឡេង និងបែបផែនដែលបានរក្សាទុករបស់វា នឹងត្រូវយកមកប្រើដោយស្វ័យប្រវត្តិ ដោយជំនួសលើការកំណត់លំនាំដើមទូទៅ។

**Clear Audio Profile** — removes the saved audio profile from the selected station. After clearing, the station reverts to the global volume and effects settings. This button is only active when the selected station already has a saved profile.
**សម្អាតទម្រង់សំឡេង** — លុបទម្រង់សំឡេងដែលបានរក្សាទុកចេញពីស្ថានីយវិទ្យុដែលបានជ្រើសរើស។ បន្ទាប់ពីការសំអាត ស្ថានីយវិទ្យុនឹងត្រឡប់ទៅប្រើការកំណត់កម្រិតសំឡេង និងបែបផែនទូទៅវិញ។ ប៊ូតុងនេះដំណើរការតែនៅពេលដែលស្ថានីយវិទ្យុដែលបានជ្រើសរើសមានប្រវត្តិកំណត់ដែលបានរក្សាទុករួចហើយ។

Both buttons are located below the favourites list and are only enabled when a station in the list is selected.
ប៊ូតុងទាំងពីរមានទីតាំងនៅខាងក្រោមបញ្ជីចំណូលចិត្ត ហើយត្រូវបានបើកតែនៅពេលស្ថានីយក្នុងបញ្ជីត្រូវបានជ្រើសរើសប៉ុណ្ណោះ។

## Music Recognition
## ការស្វែងរកបទចម្រៀង ឬតន្ត្រីដែលមិនស្គាល់ចំណងជើង

Pressing `Ctrl+Win+I` three times triggers Shazam-based music recognition for the currently playing stream. Recognition only starts when no ICY metadata (track info broadcast by the station) is available; if metadata is present, it is copied to the clipboard instead.
ចុច `Ctrl+Win+I` បីដង ចាប់ផ្តើមការស្វែងរកបទចម្រៀង ឬតន្ត្រីដែលមិនស្គាល់ចំណងជើងដោយប្រើកម្មវិធី Shazam សម្រាប់ការផ្សាយដែលកំពុងចាក់សំឡេង។ ការស្វែងរកចាប់ផ្តើមតែនៅពេលដែលគ្មានទិន្នន័យមេតា ICY  ដែលមាន (ព័ត៌មានអំពីបទចម្រៀង ឬតន្ត្រីដែលផ្សាយដោយស្ថានីវិទ្យុ) ប៉ុណ្ណោះ ហើយប្រសិនបើទិន្នន័យមេតាមានវត្តមាន វាត្រូវបានចម្លងទៅ clipboard ជំនួសវិញ។

Recognition works as follows: a short audio sample is captured from the stream using ffmpeg, the Shazam fingerprinting algorithm is applied, and the result is sent to Shazam's servers. If recognition succeeds, the track title, artist, album and release year are announced by NVDA and automatically copied to the clipboard. If the **Save liked songs to a text file** option is enabled, the recognition result is also appended to `likedSongs.txt`.
ការទទួលស្គាល់ដំណើរការដូចខាងក្រោម: គំរូសំឡេងខ្លីមួយត្រូវបានថតចេញពីស្ទ្រីមដោយប្រើ ffmpeg, អាលហ្គោរីតសម្គាល់ក្រយៅដៃរបស់ Shazam ត្រូវបានយកមកអនុវត្ត ហើយលទ្ធផលត្រូវបានបញ្ជូនទៅម៉ាស៊ីនមេរបស់ Shazam។ ប្រសិនបើការទទួលស្គាល់ជោគជ័យ ចំណងជើងបទចម្រៀង ឬតន្ត្រី សិល្បៈ អាល់ប៊ុម និងឆ្នាំចេញផ្សាយត្រូវបានប្រកាសដោយ NVDA និងចម្លងដោយស្វ័យប្រវត្តិទៅកាន់ clipboard។ ប្រសិនបើជម្រើស **រក្សាទុកបទចម្រៀងដែលចូលចិត្តទៅក្នុងឯកសារអត្ថបទ** ត្រូវបានបើក លទ្ធផលទទួលស្គាល់ក៏ត្រូវបានបន្ថែមទៅ `likedSongs.txt` ផងដែរ។

**Audio feedback:** Two rising beeps sound when recognition starts, and two falling beeps when it ends. A short beep plays every 2 seconds while the process is running.
**ការឆ្លើយតបជាសំឡេង:** សំឡេងប៊ីបកើនឡើងពីរនៅពេលការទទួលស្គាល់ចាប់ផ្តើម និងសំឡេងប៊ីបពីរទៀតនៅពេលវាបញ្ចប់។ សំឡេងប៊ីបខ្លីបន្លឺឡើងរៀងរាល់២ វិនាទី ខណៈពេលដែលដំណើរការកំពុងដំណើរការ។

**Requirement:** ffmpeg.exe is required. An ffmpeg.exe placed in the add-on folder is used automatically; if it is in a different location, the path can be set in Settings. Download ffmpeg from [ffmpeg.org](https://ffmpeg.org/download.html).
**តម្រូវការ:** ffmpeg.exe ត្រូវបានទាមទារ។ ffmpeg.exe ដែលដាក់ក្នុងថតនៃកម្មវិធីជំនួយ ត្រូវបានប្រើដោយស្វ័យប្រវត្តិ ហើយប្រសិនបើវាស្ថិតនៅក្នុងទីតាំងផ្សេង path អាចត្រូវបានកំណត់នៅក្នុងការកំណត់។

## Audio Mirror
## ការចម្លងសំឡេង

The `Ctrl+Win+M` shortcut mirrors the currently playing stream to a second audio output device simultaneously. This is useful for listening on two different devices at the same time, such as speakers and headphones.
គ្រាប់ចុចរហ័ស `Ctrl+Win+M` ចម្លងការផ្សាយសំឡេងបច្ចុប្បន្នទៅឧបករណ៍បញ្ចេញសំឡេងទីពីរក្នុងពេលដំណាលគ្នា។ វាមានប្រយោជន៍សម្រាប់ការស្តាប់នៅលើឧបករណ៍ពីរផ្សេងគ្នាក្នុងពេលតែមួយ ដូចជាឧបករណ៍បំពងសម្លេង និងកាស។

On first press, a selection dialog listing the available output devices appears. Once a device is chosen, mirroring begins and main playback continues uninterrupted. Pressing the shortcut again stops mirroring.
នៅពេលចុចដំបូង ប្រអប់ជ្រើសរើសដែលរាយបញ្ជីឧបករណ៍បញ្ចេញសំឡេងដែលមាននឹងលេចឡើង។ នៅពេលដែលឧបករណ៍មួយត្រូវបានជ្រើសរើស ការចម្លងសំឡេងចាប់ផ្តើម ហើយការចាក់បន្តដោយគ្មានការរំខាន។ ការចុចគ្រាប់ចុចម្ដងទៀតនឹងបញ្ឈប់ការចម្លងសំឡេង។

**Use cases:**
**ករណីប្រើប្រាស់:**
- **Speakers + headphones** — Let a guest follow the same broadcast on headphones while you listen through the computer speakers.
- **ឧបករណ៍បំពងសម្លេង + កាស** — អនុញ្ញាតឱ្យភ្ញៀវតាមដានការផ្សាយដូចគ្នានៅលើកាស នៅពេលដែលអ្នកស្តាប់តាមរយៈឧបករណ៍បំពងសំឡេងរបស់កុំព្យូទ័រ។
- **Recording setup** — Route the main output to speakers and the second output to an external recorder or audio interface for external capture.
- **ការរៀបចំថតសំឡេង** — បញ្ជូនលទ្ធផលមេទៅកាន់ឧបករណ៍បំពងសំឡេង និងលទ្ធផលទីពីរទៅកាន់ឧបករណ៍ថតសំឡេងខាងក្រៅ ឬផ្ទៃកម្មវិធីសំឡេងសម្រាប់ចាប់សញ្ញាសំឡេងខាងក្រៅ។
- **Multi-room** — Play through a Bluetooth speaker and the built-in speaker simultaneously; no extra software needed to carry audio to another room.
- **បន្ទប់ក្នុងចំនួនច្រើន** — ចាក់សំឡេងតាមរយៈឧបករណ៍បំពងសម្លេងប៊្លូធូស និងឧបករណ៍បំពងសំឡេងដែលភ្ជាប់មកជាមួយក្នុងពេលដំណាលគ្នា ហើយមិនចាំបាច់មានកម្មវិធីបន្ថែមដើម្បីយកសំឡេងទៅបន្ទប់ផ្សេងទេ។
- **Remote monitoring** — In a screen-sharing or remote desktop session, both the local and remote sides can hear the same stream simultaneously.
- **ការត្រួតពិនិត្យពីចម្ងាយ** — នៅក្នុងផ្នែកចែករំលែកអេក្រង់ ឬកុំព្យូទ័រពីចម្ងាយ ទាំងផ្នែកនៅនឹងកន្លែង និងពីចម្ងាយអាចស្តាប់ការផ្សាយតែមួយក្នុងពេលដំណាលគ្នា។

> **Note:** Audio mirroring is only available when the BASS backend is active. If the volume is changed while mirroring is active, both outputs are updated simultaneously.
> **ចំណាំ:** ការចម្លងសំឡេងអាចធ្វើទៅបាន លុះត្រាតែផ្នែកខាងក្រោយមូលដ្ឋានមានដំណើរការប៉ុណ្ណោះ។ ប្រសិនបើកម្រិតសំឡេងត្រូវបានផ្លាស់ប្តូរនៅពេលការចម្លងសំឡេងកំពុងមានដំណើរការ នោះលទ្ធផលទាំងពីរត្រូវបានធ្វើបច្ចុប្បន្នភាពក្នុងពេលដំណាលគ្នា។

## Recording
## ការថតសំឡេង

Recordings are saved to `Documents\FreeRadio Recordings\` by default. The filename includes the station name (or song title, in song recording mode) and the recording start time. The recordings folder can be changed at any time from NVDA Menu → Preferences → Settings → FreeRadio → **Recordings folder**. Because the recording engine connects directly to the stream, the audio is written to disk as received — no processing or re-encoding is applied; recording quality is identical to the broadcast quality.
ការថតសំឡេងត្រូវបានរក្សាទុកនៅក្នុង `Documents\FreeRadio Recordings\` តាមលំនាំដើម។ ឈ្មោះឯកសាររួមបញ្ចូលឈ្មោះស្ថានីយ៍វិទ្យុ (ឬចំណងជើងបទចម្រៀង នៅក្នុងម៉ូដថតបទចម្រៀង) និងពេលវេលាចាប់ផ្តើមថត។ ថតឯកសារអាចផ្លាស់ប្តូរបានគ្រប់ពេលពីក្នុងម៉ឺនុយរបស់ NVDA → ចំណូលចិត្ត → ការកំណត់ → FreeRadio → **ថតឯកសារ**. ដោយសារតែកម្មវិធីថតភ្ជាប់ដោយផ្ទាល់ទៅការផ្សាយសំឡេង សំឡេងត្រូវបានសរសេរទុកក្នុងថាសដូចដែលបានទទួល ហើយមិនមានការកែច្នៃ ឬបំប្លែងកូដណាមួយត្រូវបានដាក់អនុវត្តនោះទេ ហើយគុណភាពថតគឺដូចគ្នាបេះបិទទៅនឹងគុណភាពនៃការផ្សាយ។

**Instant recording:** While a station is playing, press `Ctrl+Win+E` once. Press again to stop. Playback continues uninterrupted throughout.
**ការថតសំឡេងភ្លាមៗ:** ខណៈពេលដែលស្ថានីយ៍កំពុងចាក់សំឡេង សូមចុច `Ctrl+Win+E` ម្តង។ ចុចម្តងទៀតដើម្បីបញ្ឈប់។ ការចាក់នៅតែបន្តដោយមិនមានការរំខាន។

**Song recording:** Press `Ctrl+Win+E` **twice** in quick succession while a station that broadcasts ICY metadata is playing. The recording starts immediately and is named after the current track title. When the track changes, the recording stops automatically and NVDA announces the saved filename. If you want to end the recording early before the track finishes, press `Ctrl+Win+E` twice again. If the current station does not broadcast ICY metadata, song recording is not available and NVDA will inform you.
**ការថតចម្រៀង:** សូមចុច `Ctrl+Win+E` **ពីរដង** ឱ្យបានញាប់ជាបន្តបន្ទាប់ ខណៈពេលដែលស្ថានីយ៍វិទ្យុដែលផ្សាយទិន្នន័យមេតា ICY កំពុងចាក់។ ការថតសំឡេងចាប់ផ្តើមភ្លាមៗ ហើយត្រូវបានដាក់ឈ្មោះតាមចំណងជើងបទចម្រៀង ឬតន្ត្រីបច្ចុប្បន្ន។ នៅពេលដែលបទចម្រៀង ឬតន្ត្រីផ្លាស់ប្តូរ ការថតសំឡេងឈប់ដោយស្វ័យប្រវត្តិ ហើយ NVDA នឹងប្រកាសឈ្មោះឯកសារដែលបានរក្សាទុក។ ប្រសិនបើអ្នកចង់បញ្ចប់ការថតសំឡេងលឿនមុនពេលបទចម្រៀង ឬតន្ត្រីបញ្ចប់ សូមចុច `Ctrl+Win+E` ពីរដងទៀត។ ប្រសិនបើស្ថានីយវិទ្យុបច្ចុប្បន្នមិនផ្សាយទិន្នន័យមេតារបស់ ICY ការថតបទចម្រៀងមិនមានទេ ហើយ NVDA នឹងជូនដំណឹងដល់អ្នក។

**Scheduled recording:** Open the Recording tab in the browser. Select a station from your favourites, enter the start time in HH:MM format and the duration in minutes, then choose a recording mode:
**ការថតសំឡេងតាមកាលកំណត់:** បើកផ្ទាំងថតសំឡេងនៅក្នុងកម្មវិធីរុករក។ ជ្រើសរើសស្ថានីយ៍វិទ្យុមួយពីចំណូលចិត្តរបស់អ្នក បញ្ចូលពេលវេលាចាប់ផ្តើមជាទម្រង់ HH:MM និងរយៈពេលគិតជានាទី បន្ទាប់មកជ្រើសរើសម៉ូដថតសំឡេង:

- **Record while listening** — plays and records simultaneously. A playback backend is started using the BASS → VLC → PotPlayer → Windows Media Player priority order.
- **ថតសំឡេងពេលកំពុងស្តាប់** — ចាក់សំឡេង និងថតក្នុងពេលដំណាលគ្នា។ ការចាក់ត្រូវបានចាប់ផ្តើមដោយប្រើ BASS → VLC → PotPlayer → Windows Media Player ជាលំដាប់អាទិភាព។
- **Record only** — records silently in the background without any audio output; the recording engine connects directly to the stream.
- **ថតសំឡេងតែមួយមុខងារប៉ុណ្ណោះ** — ថតដោយស្ងៀមស្ងាត់នៅក្នុងផ្ទៃខាងក្រោយដោយគ្មានលទ្ធផលសំឡេងណាមួយ ចំណែកឯម៉ាស៊ីនថតភ្ជាប់ដោយផ្ទាល់ទៅស្ទ្រីម។

If the entered time has already passed, the recording is scheduled for the following day. NVDA announces when a recording starts and when it finishes.
ប្រសិនបើពេលវេលាដែលបានបញ្ចូលបានកន្លងផុតទៅហើយ ការថតត្រូវបានកំណត់ពេលសម្រាប់ថ្ងៃបន្ទាប់។ NVDA នឹងប្រកាសនៅពេលដែលការថតសំឡេងចាប់ផ្តើម និងនៅពេលដែលវាបញ្ចប់។

## Timer
## កម្មវិធីកំណត់ម៉ោង

Open the Timer tab in the station browser (`Alt+4`). Two types of timer can be added:
បើកផ្ទាំងកម្មវិធីកំណត់ម៉ោងនៅក្នុងកម្មវិធីរុករកតាមអ៊ីនធឺណិត (`Alt+4`). កម្មវិធីកំណត់ម៉ោងពីរប្រភេទនឹងអាចត្រូវបានបន្ថែម:

**Alarm — start radio:** Automatically starts playing a selected station from your favourites at the specified time. Choose a station and enter the time in HH:MM format.
**សំឡេងរោទិ៍ - ចាប់ផ្តើមវិទ្យុ:** ចាប់ផ្តើមចាក់សំឡេងស្ថានីយ៍វិទ្យុដែលបានជ្រើសរើសដោយស្វ័យប្រវត្តិពីចំណូលចិត្តរបស់អ្នកនៅពេលជាក់លាក់មួយ។ សូមជ្រើសរើសស្ថាននីវិទ្យុ  ហើយបញ្ចូលពេលវេលាក្នុងទម្រង់ជា HH:MM។

**Sleep — stop radio:** Stops playback at the specified time. When the timer fires, volume is gradually reduced over 60 seconds before playback stops. No station selection is needed; just enter the time.
**ផ្អាក - បញ្ឈប់សំឡេងវិទ្យុ:** បញ្ឈបការចាក់តាមពេលដែលបានកំណត់។ នៅពេលឧបករណ៍រាប់ថយក្រោយដល់ពេលដែលបានកំណត់ កម្រិតសំឡេងនឹងត្រូវបានបន្ថយបន្តិចម្ដងៗក្នុងរយៈពេល៦០ វិនាទី មុនពេលការចាក់សំឡេងត្រូវបញ្ឈប់ទាំងស្រុង។  មិនចាំបាច់ជ្រើសរើសស្ថាននីវិទ្យុនោះទេ គ្រាន់តែបញ្ចូលពេលវេលាជាការស្រេច។

For both types, if the entered time has already passed the action is scheduled for the following day. Pending timers are listed in the tab; select one and press the Remove Selected Timer button to cancel it.
សម្រាប់ប្រភេទទាំងពីរ ប្រសិនបើពេលវេលាដែលបានបញ្ចូលបានកន្លងផុតទៅហើយ សកម្មភាពត្រូវបានកំណត់ពេលសម្រាប់ថ្ងៃបន្ទាប់។ កម្មវិធីកំណត់ម៉ោងដែលមិនទាន់សម្រេចត្រូវបានរាយបង្ហាញក្នុងផ្ទាំង ហើយសូមជ្រើសរើសយកកម្មវិធីមួយ និងចុចប៊ូតុង Remove Selected Timer ដើម្បីបោះបង់វា។

## Settings
## ការកំណត់

The following options can be configured from NVDA Menu → Preferences → Settings → FreeRadio:
ជម្រើសខាងក្រោមអាចត្រូវបានកំណត់រចនាសម្ព័ន្ធពីក្នុងម៉ឺនុយ NVDA → ចំណូលចិត្ត → ការកំណត់ → FreeRadio:

| Option | Description |
| ជម្រើស | ការពិពណ៌នា |
|---|---|
| Audio output device (BASS backend) | Sets the audio output device for radio playback. The list includes all BASS-compatible devices on the system plus a "System default" option. Changes are applied immediately on save; if the selected device is disconnected, the add-on automatically falls back to the system default and announces the change. Only active when the BASS backend is in use. |
| ឧបករណ៍បញ្ចេញសំឡេង (BASS backend) | កំណត់ឧបករណ៍បញ្ចេញសំឡេងសម្រាប់ការចាក់សំឡេងវិទ្យុ។ បញ្ជីនេះរួមបញ្ចូលទាំងឧបករណ៍ទាំងអស់នៅលើប្រព័ន្ធដែលទ្រទ្រង់ BASS និងជម្រើស "ប្រព័ន្ធដើម (System default)"។ ការផ្លាស់ប្តូរនឹងត្រូវអនុវត្តភ្លាមៗនៅពេលរក្សាទុក។ ប្រសិនបើឧបករណ៍ដែលបានជ្រើសរើសត្រូវដាច់ការតភ្ជាប់ កម្មវិធីជំនួយ (Add-on) នឹងផ្លាស់ប្តូរទៅប្រើប្រព័ន្ធដើមដោយស្វ័យប្រវត្តិ ហើយជូនដំណឹងពីការផ្លាស់ប្តូរនេះ។ វាដំណើរការតែនៅពេល BASS backend កំពុងត្រូវ បានប្រើប្រាស់ប៉ុណ្ណោះ។ |
| Volume | Sets the add-on's starting volume (0–200). Changes made during playback with `Ctrl+Win+↑` / `Ctrl+Win+↓` are also reflected here. |
| កម្រិតសំឡេង | កំណត់កម្រិតសំឡេងចាប់ផ្ដើមរបស់កម្មវិធីជំនួយ (០–២០០)។ ការផ្លាស់ប្តូរដែលបានធ្វើឡើងកំឡុងពេលចាក់ដោយប្រើ Ctrl+Win+↑ / Ctrl+Win+↓ ក៏នឹងបង្ហាញនៅទីនេះផងដែរ។ |
| Default audio effect | Sets the audio effect applied when NVDA starts or a station begins playing. The selected effect corresponds to the Effects list in the Station Browser. Only active when the BASS backend is in use. |
| បែបផែនសំឡេងអូឌីយ៉ូលំនាំដើម | កំណត់បែបផែនសំឡេងអូឌីយ៉ូ (Audio effect) ដែលត្រូវប្រើនៅពេល NVDA ចាប់ផ្តើម ឬនៅពេលស្ថានីយវិទ្យុចាប់ផ្តើមចាក់។ បែបផែនដែលបានជ្រើសរើសគឺត្រូវគ្នាទៅនឹងបញ្ជីបែបផ៉ែន (Effects list) នៅក្នុងកម្មវិធីរុករកស្ថានីយវិទ្យុ (Station Browser)។ វាមានដំណើរការតែនៅពេល BASS backend កំពុងត្រូវបានប្រើប្រាស់ប៉ុណ្ណោះ។ |
| Station switch transition (BASS backend) | Controls the transition behaviour when switching between stations. **Instant cut** (default) stops the previous station immediately before the new one starts. **Short crossfade (1 second)** and **Normal crossfade (2 seconds)** start the new station immediately with no gap, then gradually fade out the previous station in the background once the new stream is confirmed active. Has no effect and no performance impact when set to Instant cut. Only available when the BASS backend is in use. |
| ការផ្លាស់ប្តូរស្ថានីយ៍វិទ្យុ (BASS backend) | គ្រប់គ្រងឥរិយាបថនៃការផ្លាស់ប្តូរនៅពេលប្តូររវាងស្ថានីយវិទ្យុ។ **កាត់ភ្លាមៗ** (លំនាំដើម) បញ្ឈប់ស្ថានីយវិទ្យុមុនភ្លាមៗ មុនពេលស្ថានីយវិទ្យុថ្មីចាប់ផ្តើម។ **ការរលាយសំឡេងឆ្លាស់គ្នាខ្លី (Short crossfade) (១ វិនាទី)** និង **ការរលាយសំឡេងឆ្លាស់គ្នាធម្មតា (Normal crossfade) (២ វិនាទី)** ចាប់ផ្តើមស្ថានីយ៍ថ្មីភ្លាមៗដោយគ្មានគម្លាត បន្ទាប់មកបន្ថយសំឡេងបន្តិចម្តងៗនូវស្ថានីយវិទ្យុមុនក្នុងផ្ទៃខាងក្រោយ នៅពេលដែលការផ្សាយថ្មីត្រូវបានបញ្ជាក់ថាមានដំណើរការ។ គ្មានផលប៉ះពាល់ និងមិនប៉ះពាល់ដល់ប្រសិទ្ធភាពដំណើរការទេ នៅពេលកំណត់ទៅជាបែបកាត់ភ្លាមៗ។ អាចប្រើបានតែនៅពេល BASS backend កំពុងត្រូវបានប្រើប្រាស់ប៉ុណ្ណោះ។ |
| Resume last station on NVDA startup | When enabled, the last played station automatically restarts every time NVDA starts. |
| បន្តស្ថានីយ៍ចុងក្រោយនៅពេលចាប់ផ្តើម NVDA | នៅពេលបើកដំណើរការ ស្ថានីយ៍ដែលបានចាក់ចុងក្រោយនឹងចាប់ផ្តើមឡើងវិញដោយស្វ័យប្រវត្តិរាល់ពេលដែល NVDA ចាប់ផ្តើម។ |
| Auto-announce track changes (ICY metadata) | When enabled, NVDA automatically reads the new track name each time it changes on a station that broadcasts ICY metadata. The first track is also announced immediately when switching to a new station. Disabled by default. |
| អានប្រាប់ដោយស្វ័យប្រវត្តិអំពីការផ្លាស់ប្តូរបទចម្រៀង ឬតន្ត្រី (ទិន្នន័យមេតា ICY) | នៅពេលបើកដំណើរការ NVDA នឹងអានឈ្មោះបទចម្រៀង ឬតន្ត្រីថ្មីដោយស្វ័យប្រវត្តិរាល់ពេលដែលវាផ្លាស់ប្តូរនៅលើស្ថានីយ៍វិទ្យុដែលផ្សាយទិន្នន័យមេតា ICY។ បទចម្រៀង ឬតន្ត្រីដំបូងក៏ត្រូវបានប្រកាសភ្លាមៗផងដែរ នៅពេលប្តូរទៅស្ថានីយ៍ថ្មី។ បើតាមលំនាំដើម វាត្រូវបានបិទដំណើរការ។ |
| Mute notifications | When enabled, NVDA does not announce station changes, playback state changes (play, pause, stop), or recording events (started, stopped, finished). Error messages, favourites feedback, music recognition results, and update notifications are not affected. Can also be toggled on the fly via an unassigned input gesture. Disabled by default. |
| បិទសំឡេងការជូនដំណឹង | នៅពេលបើកដំណើរការ NVDA មិនអានប្រាប់ពីការផ្លាស់ប្តូរស្ថានីយ៍វិទ្យុ ការផ្លាស់ប្តូរស្ថានភាពចាក់សំឡេង (ចាក់សំឡេង ផ្អាក បញ្ឈប់) ឬការថតព្រឹត្តិការណ៍ (បានចាប់ផ្តើម បញ្ឈប់ បញ្ចប់) ទេ។ សារកំហុស មតិកែលម្អលើចំណូលចិត្ត លទ្ធផលនៃការស្វែងរកបទចម្រៀង ឬតន្ត្រីដែលមិនស្គាល់ចំណងជើង និងការជូនដំណឹងអំពីការធ្វើបច្ចុប្បន្នភាព មិនត្រូវបានប៉ះពាល់ទេ។ វាក៏អាចត្រូវបានបិទ ឬបើកភ្លាមៗតាមរយៈចលនាថ្នាក់បញ្ចូលដែលមិនទាន់បានកំណត់ផងដែរ។ បើតាមលំនាំដើម វាត្រូវបានបិទដំណើរការ។ |
| Save liked songs to a text file | When enabled, track info copied to the clipboard by pressing `Ctrl+Win+I` three times is also appended to `Documents\FreeRadio Recordings\likedSongs.txt`. If no ICY metadata is available, the Shazam recognition result is saved to the same file. Disabled by default. |
| រក្សាទុកបទចម្រៀងដែលចូលចិត្តទៅជាឯកសារអត្ថបទ | នៅពេលបើកដំណើរការ ព័ត៌មានបទចម្រៀង ឬតន្ត្រីដែលត្រូវបានចម្លងទៅ clipboard ដោយចុច `Ctrl+Win+I` ចំនួនបីដងក៏ត្រូវបានភ្ជាប់ជាមួយ `Documents\FreeRadio Recordings\likedSongs.txt` ផងដែរ. ប្រសិនបើមិនមានទិន្នន័យមេតា ICY ទេ លទ្ធផលនៃការស្វែងរកដោយ Shazam ត្រូវបានរក្សាទុកទៅក្នុងឯកសារដូចគ្នា។ បើតាមលំនាំដើម វាត្រូវបានបិទដំណើរការ។ |
| When Ctrl+Win+P is pressed with no active playback | Determines what happens when this shortcut is pressed and nothing is playing: start the last station or open the favourites list. |
| នៅពេលដែលចុច Ctrl+Win+P ដោយមិនមានការចាក់ដំណើរការ | កំណត់អ្វីដែលកើតឡើងនៅពេលដែលគ្រាប់ចុចរហ័សនេះត្រូវបានចុច ហើយគ្មានអ្វីកំពុងចាក់: ចាប់ផ្តើមស្ថានីយ៍វិទ្យុចុងក្រោយ ឬបើកបញ្ជីចំណូលចិត្ត។ |
| When Ctrl+Win+P is pressed twice | Selects what happens when the shortcut is pressed twice in quick succession: do nothing, open the favourites list, open the recording tab or open the timer tab. When "do nothing" is selected, the first press responds instantly with no delay. |
| នៅពេលដែលចុច Ctrl+Win+P ចំនួនពីរដង | ជ្រើសរើសអ្វីដែលនឹងកើតឡើងនៅពេលដែលគ្រាប់ចុចរហ័សត្រូវបានចុចពីរដងជាប់ៗគ្នាយ៉ាងរហ័ស: មិនធ្វើអ្វីទាំងអស់ បើកបញ្ជីចំណូលចិត្ត បើកផ្ទាំងថត ឬបើកផ្ទាំងកម្មវិធីកំណត់ម៉ោង។ នៅពេលជ្រើសរើសយក "មិនធ្វើអ្វីទាំងអស់" ការចុចលើកដំបូងឆ្លើយតបភ្លាមៗដោយគ្មានការពន្យារពេល។ |
| When Ctrl+Win+P is pressed three times | Selects what happens when the shortcut is pressed three times in quick succession: do nothing, open the favourites list, open the search tab, open the recording tab or open the timer tab. |
| នៅពេលដែលចុច Ctrl+Win+P ចំនួនបីដង | ជ្រើសរើសអ្វីដែលនឹងកើតឡើងនៅពេលដែលគ្រាប់ចុចរហ័សត្រូវបានចុចបីដងជាប់ៗគ្នាយ៉ាងរហ័ស: មិនធ្វើអ្វីទាំងអស់ បើកបញ្ជីចំណូលចិត្ត បើកផ្ទាំងស្វែងរក បើកផ្ទាំងថត ឬបើកផ្ទាំងកម្មវិធីកំណត់ម៉ោង។ |
| Check for updates automatically | When enabled, a background update check runs each time NVDA starts; you are notified if a new version is found. When disabled, automatic checks stop but manual checks remain available. |
| ពិនិត្យមើលការធ្វើបច្ចុប្បន្នភាពដោយស្វ័យប្រវត្តិ | នៅពេលបើកដំណើរការ ការត្រួតពិនិត្យការធ្វើបច្ចុប្បន្នភាពផ្ទៃខាងក្រោយនឹងដំណើរការរាល់ពេលដែល NVDA ចាប់ផ្តើម ហើយអ្នកនឹងត្រូវបានជូនដំណឹង ប្រសិនបើរកឃើញកំណែថ្មី។ នៅពេលបិទដំណើរការ ការត្រួតពិនិត្យដោយស្វ័យប្រវត្តិនឹងឈប់ ប៉ុន្តែការត្រួតពិនិត្យដោយដៃផ្ទាល់នៅតែអាចប្រើបាន។ |
| ffmpeg.exe path | Path to the ffmpeg.exe used for music recognition. If left blank, an ffmpeg.exe in the add-on folder is used automatically. |
| ផ្លូវ ffmpeg.exe | ផ្លូវទៅកាន់ ffmpeg.exe ត្រូវប្រើសម្រាប់ការស្វែងរកបទចម្រៀង ឬតន្ត្រីដែលមិនស្គាល់ចំណងជើង។ ប្រសិនបើទុកឱ្យទំនេរចោល នោះ ffmpeg.exe ដែលមាននៅក្នុងថតកម្មវិធីជំនួយ (add-on folder) នឹងត្រូវយកមកប្រើដោយស្វ័យប្រវត្តិ។ |
| VLC path | If VLC is not installed or is in a non-standard location, the full path to the executable can be entered here. |
| wmplayer.exe path | Enter the path to Windows Media Player here if needed. |
| PotPlayer path | If PotPlayer is in a non-standard location, its path can be entered here. |
| Recordings folder | Sets the folder where recorded files are saved. If left blank, the default location `Documents\FreeRadio Recordings\` is used. A Browse button lets you select the folder interactively. Changes take effect immediately after saving. |
| Disable internet connectivity check before playing | Recommended for users who experience a delay before a station starts playing. Also useful when DNS is blocked. |

## Mute Notifications

When **Mute notifications** is enabled in Settings, NVDA silences the following automatic announcements:

- Station name when a new station starts playing
- Playback state changes: play, pause, stop
- Recording events: started, stopped, finished (instant, song and scheduled recordings)
- ICY track change announcements, even when **Auto-announce track changes** is also enabled

The following announcements are intentionally **not** affected: error messages, favourites feedback (added / already in list), music recognition results, and update notifications.

The setting can be toggled from NVDA Menu → Preferences → Settings → FreeRadio, or instantly at any time via an unassigned input gesture (assign one from NVDA Menu → Preferences → Input Gestures → FreeRadio). When toggled, NVDA announces "Notifications muted" or "Notifications unmuted" once to confirm the change.

## Auto-announce Track Changes

When the **Auto-announce track changes** option is enabled in Settings, FreeRadio checks the active station's ICY metadata stream in the background approximately every 5 seconds. When the track changes, the new title is automatically read by NVDA — no keypress required.

When switching to a new station, the first track info is announced as soon as the connection is established. If you switch to a station that does not broadcast ICY metadata, the system stays silent and the previous station's track info is not repeated.

This feature is disabled by default and can be toggled from NVDA Menu → Preferences → Settings → FreeRadio.

## Liked Songs

When the **Save liked songs to a text file** option is enabled, track info copied to the clipboard by pressing `Ctrl+Win+I` three times is also appended line by line to `Documents\FreeRadio Recordings\likedSongs.txt`.

On stations that broadcast ICY metadata, the track title and artist are saved directly. On stations without ICY metadata, the Shazam recognition result is saved to the same file — both sources share the same list. The file is created automatically if it does not exist; each entry is appended to the end of the file and previous entries are never deleted.

## Liked Songs Tab

The **Liked Songs** tab in the station browser displays all tracks saved in `likedSongs.txt`. The list is automatically reloaded from the file each time the tab is opened.

Selecting a track from the list enables the following actions:

- **Play on Spotify:** Tries to open the Spotify desktop app directly. If the app is not installed, falls back to the Spotify website and automatically starts playing the first result.
- **Play on YouTube (`Alt+O`):** Searches YouTube for the selected track and opens the results in the default browser.
- **Remove (`Alt+M`):** Deletes the selected track from `likedSongs.txt` and updates the list. The `Delete` key also triggers this button when the list is focused.
- **Refresh (`Alt+E`):** Reloads the list from the file.

The Spotify, YouTube, and Remove buttons are only enabled when a real track is selected in the list.

## Playback

The add-on selects a playback backend using the following priority order:

1. **BASS** — the default and primary backend. No separate installation is required; it is bundled with the add-on. BASS sends audio directly to the Windows audio stack and appears in the Windows volume mixer as an independent audio source named "pythonw.exe", separate from NVDA. This means FreeRadio audio flows on a completely separate channel from NVDA speech: the radio does not cut out, mix with, or get affected by NVDA's own audio settings while NVDA is speaking. The user can adjust the radio volume independently from NVDA in the Windows Volume Mixer. Supports HTTP, HTTPS and most embedded stream formats. Audio mirroring is only available with this backend.
2. **VLC** — takes over if BASS fails. Searched automatically in common installation locations, user profile folders and the system PATH.
3. **PotPlayer** — tried if VLC is not found. Searched automatically in common installation locations.
4. **Windows Media Player** — used as a last resort; requires the WMP component to be installed on the system.

## Update Check

FreeRadio automatically checks for new versions via GitHub.

**Automatic check:** Runs silently in the background 15 seconds after NVDA starts. If a new version is found, you are notified; if none is found, no message is shown.

**Manual check:** Can be triggered on demand from NVDA Tools → FreeRadio → **Check for Updates…**. When started this way, the result is announced even if the version is up to date.

**When an update is found:** A dialog opens showing the version number and your installed version.

- If a directly downloadable `.nvda-addon` file is available on the GitHub release, a **Download and Install** button is shown. Once confirmed, the file is downloaded in the background, NVDA announces when the download starts, and NVDA's own installation screen opens automatically.
- If no direct download link is available, an **Open Page** button is shown and the GitHub release page opens in the default browser.

**To disable automatic checks:** Turn off the **Check for updates automatically** option from NVDA Menu → Preferences → Settings → FreeRadio.

## License

GPL v2