from crawling import run_spider
from mailing import send_mails


def main():
    run_spider()
    send_mails()


if __name__ == '__main__':
    main()
