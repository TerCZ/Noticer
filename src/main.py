"""Combine crawling and mailing part together."""
import sys

from crawling import run_spider
from mailing import send_mails, send_mails_test


def main():
    """Main procedure."""
    run_spider()
    if len(sys.argv) > 1:
        send_mails_test()
    else:
        send_mails()


if __name__ == '__main__':
    main()
