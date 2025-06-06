import requests
import time
import json
import telebot
from bs4 import BeautifulSoup
import os

# --- Configuration ---
# Get your BotFather token from environment variables or replace directly
BOT_TOKEN = os.getenv('BOT_TOKEN', None)
if not BOT_TOKEN:
    exit("Insert a valid BOT_TOKEN")
# List of Telegram Chat IDs to send notifications to
# You can get these by sending a message to your bot and then checking:
# https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
CHAT_IDS = [ele.strip() for ele in os.getenv("CHAT_IDS", "").split(",") if ele.strip()]
KEY_TEXT = os.getenv("KEY_TEXT", "").upper()
if not KEY_TEXT:
    exit("Insert a valid KEY_TEXT")

REFRESH_RATE = int(os.getenv("REFRESH_RATE", "300"))

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# URL and headers for the Poliba website request
POLIBA_URL = 'https://www.poliba.it/it/views/ajax'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:138.0) Gecko/20100101 Firefox/138.0',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'it-IT,it;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'X-Requested-With': 'XMLHttpRequest',
    'Origin': 'https://www.poliba.it',
    'Sec-GPC': '1',
    'Connection': 'keep-alive',
    'Referer': 'https://www.poliba.it/it/amministrazione-e-servizi/albo-online',
    'Cookie': 'has_js=1',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'Priority': 'u=0'
}

# --- Persistent Storage for Found Tenders ---
# We'll save found tenders to a file to prevent re-notifying after a bot restart
FOUND_TENDERS_FILE = 'data/found_tenders.json'
os.makedirs("./data", exist_ok=True)

def load_found_tenders():
    """Loads previously found tenders from a JSON file."""
    if os.path.exists(FOUND_TENDERS_FILE):
        with open(FOUND_TENDERS_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def save_found_tenders(tenders_set):
    """Saves the current set of found tenders to a JSON file."""
    with open(FOUND_TENDERS_FILE, 'w') as f:
        json.dump(list(tenders_set), f)

# Load tenders when the script starts
found_tenders = load_found_tenders()

# --- Tender Checking Logic ---
def check_for_new_tenders():
    """Checks the Poliba website for new tenders containing "ISP5G"."""
    global found_tenders
    print("Checking for new tenders...")

    try:
        # Iterate through the first few pages (e.g., 3 pages)
        for page_num in range(10):
            data = {
                'view_name': 'albo_online',
                'view_display_id': 'block',
                'view_args': '',
                'view_path': 'node/3721',
                'view_base_path': '',
                'view_dom_id': 'a41f9fb34f3bbf348abc81d7ecfeecfb',
                'pager_element': '0',
                'page': str(page_num),
                'ajax_html_ids[]': [
                    'skip-link', 'header-fullwidth', 'top', 'block-block-36', 'search-block-form',
                    'edit-search-block-form--2', 'edit-actions', 'edit-submit', 'tb-megamenu-column-1',
                    'tb-megamenu-column-2', 'tb-megamenu-column-3', 'tb-megamenu-column-4',
                    'tb-megamenu-column-5', 'tb-megamenu-column-6', 'tb-megamenu-column-7',
                    'tb-megamenu-column-8', 'tb-megamenu-column-9', 'tb-megamenu-column-10',
                    'tb-megamenu-column-11', 'tb-megamenu-column-12', 'tb-megamenu-column-13',
                    'tb-megamenu-column-14', 'tb-megamenu-column-15', 'tb-megamenu-column-16',
                    'tb-megamenu-column-17', 'tb-megamenu-column-18', 'tb-megamenu-column-19',
                    'tb-megamenu-column-20', 'tb-megamenu-column-21', 'tb-megamenu-column-22',
                    'Main-Content', 'content_top', 'block-block-44', 'content', 'block-system-main',
                    'node-3721', 'block-views-albo-online-block', 'views-exposed-form-albo-online-block',
                    'edit-field-tipologia-atto-value-wrapper', 'edit-field-tipologia-atto-value',
                    'edit-field-dipartimento-struttura-value-wrapper',
                    'edit-field-dipartimento-struttura-value', 'edit-submit-albo-online', 'sidebar',
                    'block-block-57', 'menuJ', 'sidebar-menu-1', 'Content-FullWidth', 'Footer-FullWidth',
                    'footer', 'block-block-37', 'footermenup', 'footermenup', 'footermenup', 'copyright',
                    'block-block-80'
                ],
                'ajax_page_state[theme]': 'jango_sub',
                'ajax_page_state[theme_token]': 'xl2yCVw4NM0p5QtGmrXqImVXqFdfiNIcWP-XKlMDgnI',
                'ajax_page_state[css][0]': '1',
                'ajax_page_state[css][modules/system/system.base.css]': '1',
                'ajax_page_state[css][modules/aggregator/aggregator.css]': '1',
                'ajax_page_state[css][modules/book/book.css]': '1',
                'ajax_page_state[css][modules/comment/comment.css]': '1',
                'ajax_page_state[css][sites/all/modules/date/date_api/date.css]': '1',
                'ajax_page_state[css][sites/all/modules/date/date_popup/themes/datepicker.1.7.css]': '1',
                'ajax_page_state[css][sites/all/modules/date/date_repeat_field/date_repeat_field.css]': '1',
                'ajax_page_state[css][modules/field/theme/field.css]': '1',
                'ajax_page_state[css][modules/node/node.css]': '1',
                'ajax_page_state[css][modules/poll/poll.css]': '1',
                'ajax_page_state[css][modules/forum/forum.css]': '1',
                'ajax_page_state[css][sites/all/modules/views/css/views.css]': '1',
                'ajax_page_state[css][sites/all/modules/ckeditor/css/ckeditor.css]': '1',
                'ajax_page_state[css][sites/all/modules/media/modules/media_wysiwyg/css/media_wysiwyg.base.css]': '1',
                'ajax_page_state[css][sites/all/modules/ctools/css/ctools.css]': '1',
                'ajax_page_state[css][sites/all/modules/eu_cookie_compliance/css/eu_cookie_compliance.css]': '1',
                'ajax_page_state[css][sites/all/themes/jango/assets/plugins/socicon/socicon.css]': '1',
                'ajax_page_state[css][sites/all/themes/jango/assets/plugins/bootstrap-social/bootstrap-social.css]': '1',
                'ajax_page_state[css][sites/all/themes/jango/assets/plugins/font-awesome/css/font-awesome.min.css]': '1',
                'ajax_page_state[css][sites/all/themes/jango/assets/plugins/simple-line-icons/simple-line-icons.min.css]': '1',
                'ajax_page_state[css][sites/all/themes/jango/assets/plugins/animate/animate.min.css]': '1',
                'ajax_page_state[css][sites/all/themes/jango/assets/plugins/cubeportfolio/css/cubeportfolio.min.css]': '1',
                'ajax_page_state[css][sites/all/themes/jango/assets/plugins/owl-carousel/assets/owl.carousel.css]': '1',
                'ajax_page_state[css][sites/all/themes/jango/assets/plugins/fancybox/jquery.fancybox.css]': '1',
                'ajax_page_state[css][sites/all/themes/jango/assets/plugins/slider-for-bootstrap/css/slider.css]': '1',
                'ajax_page_state[css][sites/all/themes/jango/assets/plugins/ilightbox/css/ilightbox.css]': '1',
                'ajax_page_state[css][sites/all/themes/jango/css/YTPlayer.css]': '1',
                'ajax_page_state[css][sites/all/themes/jango/css/fonts.css]': '1',
                'ajax_page_state[css][sites/all/themes/jango/assets/plugins/bootstrap/css/bootstrap.css]': '1',
                'ajax_page_state[css][sites/all/themes/jango/assets/base/css/plugins.css]': '1',
                'ajax_page_state[css][sites/all/themes/jango/assets/base/css/components.css]': '1',
                'ajax_page_state[css][sites/all/themes/jango/assets/base/css/custom.css]': '1',
                'ajax_page_state[css][sites/all/themes/jango/css/drupal.css]': '1',
                'ajax_page_state[css][sites/all/themes/jango/assets/base/css/themes/default.css]': '1',
                'ajax_page_state[css][sites/all/themes/jango/jango_sub/css/custom.css]': '1',
                'ajax_page_state[js][0]': '1',
                'ajax_page_state[js][1]': '1',
                'ajax_page_state[js][sites/all/modules/eu_cookie_compliance/js/eu_cookie_compliance.js]': '1',
                'ajax_page_state[js][sites/all/modules/jquery_update/replace/jquery/1.10/jquery.min.js]': '1',
                'ajax_page_state[js][misc/jquery.once.js]': '1',
                'ajax_page_state[js][misc/drupal.js]': '1',
                'ajax_page_state[js][sites/all/modules/jquery_update/replace/ui/external/jquery.cookie.js]': '1',
                'ajax_page_state[js][sites/all/modules/jquery_update/replace/jquery.form/4/jquery.form.min.js]': '1',
                'ajax_page_state[js][misc/ajax.js]': '1',
                'ajax_page_state[js][sites/all/modules/jquery_update/js/jquery_update.js]': '1',
                'ajax_page_state[js][sites/all/modules/admin_menu/admin_devel/admin_devel.js]': '1',
                'ajax_page_state[js][public://languages/it_Y-dxfs1QQ3P6fOXNBZai201929U2R6WLuVA3N2bGU7I.js]': '1',
                'ajax_page_state[js][misc/tableheader.js]': '1',
                'ajax_page_state[js][sites/all/modules/views/js/base.js]': '1',
                'ajax_page_state[js][misc/progress.js]': '1',
                'ajax_page_state[js][sites/all/modules/views/js/ajax_view.js]': '1',
                'ajax_page_state[js][sites/all/themes/jango/assets/plugins/jquery-migrate.min.js]': '1',
                'ajax_page_state[js][sites/all/themes/jango/assets/plugins/bootstrap/js/bootstrap.min.js]': '1',
                'ajax_page_state[js][sites/all/themes/jango/assets/plugins/jquery.easing.min.js]': '1',
                'ajax_page_state[js][sites/all/themes/jango/assets/plugins/reveal-animate/wow.js]': '1',
                'ajax_page_state[js][sites/all/themes/jango/assets/plugins/cubeportfolio/js/jquery.cubeportfolio.min.js]': '1',
                'ajax_page_state[js][sites/all/themes/jango/assets/plugins/owl-carousel/owl.carousel.js]': '1',
                'ajax_page_state[js][sites/all/themes/jango/assets/plugins/counterup/jquery.waypoints.min.js]': '1',
                'ajax_page_state[js][sites/all/themes/jango/assets/plugins/counterup/jquery.counterup.min.js]': '1',
                'ajax_page_state[js][sites/all/themes/jango/assets/plugins/fancybox/jquery.fancybox.pack.js]': '1',
                'ajax_page_state[js][sites/all/themes/jango/assets/plugins/slider-for-bootstrap/js/bootstrap-slider.js]': '1',
                'ajax_page_state[js][sites/all/themes/jango/assets/plugins/zoom-master/jquery.zoom.min.js]': '1',
                'ajax_page_state[js][sites/all/themes/jango/assets/plugins/isotope/isotope.pkgd.min.js]': '1',
                'ajax_page_state[js][sites/all/themes/jango/assets/plugins/isotope/imagesloaded.pkgd.min.js]': '1',
                'ajax_page_state[js][sites/all/themes/jango/assets/plugins/isotope/packery-mode.pkgd.min.js]': '1',
                'ajax_page_state[js][sites/all/themes/jango/assets/plugins/ilightbox/js/jquery.requestAnimationFrame.js]': '1',
                'ajax_page_state[js][sites/all/themes/jango/assets/plugins/ilightbox/js/jquery.mousewheel.js]': '1',
                'ajax_page_state[js][sites/all/themes/jango/assets/plugins/ilightbox/js/ilightbox.packed.js]': '1',
                'ajax_page_state[js][sites/all/themes/jango/assets/plugins/progress-bar/progressbar.js]': '1',
                'ajax_page_state[js][sites/all/themes/jango/assets/base/js/scripts/reveal-animate/reveal-animate.js]': '1',
                'ajax_page_state[js][sites/all/themes/jango/assets/base/js/app.js]': '1',
                'ajax_page_state[js][sites/all/themes/jango/assets/base/js/components.js]': '1',
                'ajax_page_state[js][sites/all/themes/jango/assets/base/js/components-shop.js]': '1',
                'ajax_page_state[js][sites/all/themes/jango/assets/plugins/gmaps/gmaps.js]': '1',
                'ajax_page_state[js][sites/all/themes/jango/assets/plugins/gmaps/api.js]': '1',
                'ajax_page_state[js][sites/all/themes/jango/js/jquery.mb.YTPlayer.js]': '1',
                'ajax_page_state[js][sites/all/themes/jango/js/drupal.js]': '1',
                'ajax_page_state[jquery_version]': '1.10'
            }

            # Suppress SSL warnings when verify=False is used
            requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
            response = requests.post(POLIBA_URL, headers=HEADERS, data=data, verify=False)
            response.raise_for_status()  # Raise an exception for HTTP errors

            response_json = response.json()

            # Find the HTML data within the JSON response
            html_content = ""
            for command in response_json:
                if command.get("command") == "insert" and command.get("selector") == ".view-dom-id-a41f9fb34f3bbf348abc81d7ecfeecfb":
                    html_content = command["data"]
                    break

            if html_content:
                soup = BeautifulSoup(html_content, 'html.parser')
                tenders_table = soup.find('table', class_='views-table')
                if tenders_table:
                    rows = tenders_table.find('tbody').find_all('tr')
                    for row in rows:
                        title_column = row.find('td')
                        if title_column:
                            tender_title = title_column.get_text(strip=True)
                            tender_link = title_column.find('a')['href'] if title_column.find('a') else '#'
                            full_link = requests.compat.urljoin('https://www.poliba.it', tender_link)

                            if "ISP5G" in tender_title.upper() and full_link not in found_tenders:
                                message = f"🔔 **Nuovo Bando Trovato!**\n\n**Titolo:** {tender_title}\n**Link:** {full_link}"
                                # Send message to all CHAT_IDS
                                for chat_id in CHAT_IDS:
                                    try:
                                        bot.send_message(chat_id, message, parse_mode='Markdown')
                                        print(f"Notified {chat_id} about: {tender_title}")
                                    except telebot.apihelper.ApiTelegramException as e:
                                        print(f"Error sending message to {chat_id}: {e}")
                                found_tenders.add(full_link)
                                save_found_tenders(found_tenders) # Save after each new tender is found
                else:
                    print(f"No tenders table found on page {page_num}.")
            else:
                print(f"No HTML content found for tenders on page {page_num}.")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
    except json.JSONDecodeError:
        print("Error decoding JSON response.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# --- Main Loop ---
def main():
    """Main function to periodically check for tenders."""
    while True:
        check_for_new_tenders()
        # Wait for 1 hour before checking again
        print(f"Waiting for 1 hour before next check...")
        time.sleep(REFRESH_RATE)  

if __name__ == '__main__':
    main()


