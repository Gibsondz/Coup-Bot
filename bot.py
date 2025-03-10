from coup_bot import CoupBot


def main():
    bot = CoupBot("player1", "http://localhost:3000")
    bot.listen()


if __name__ == "__main__":
    main()
