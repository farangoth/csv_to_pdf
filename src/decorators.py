import time


class ProgressBarPrinter:
    def __init__(self, desc, width=40, char_block="#", char_line="-"):
        self.desc = desc
        self.width = width - len(self.desc)
        self.char_block = char_block
        self.char_line = char_line
        self.start_time = time.time()

        print(f"{self.desc} [{self.char_line * self.width}] 0.00% - 0.00s", end="")

    def update(self, progress):
        run_time = time.time() - self.start_time
        done = self.char_block * int(progress * self.width)
        to_do = self.char_line * int((1 - progress) * self.width)
        print(f"\r{self.desc} [{done}{to_do}] {progress:.2%} - {run_time:.3}s", end="")

    def end_bar(self):
        run_time = time.time() - self.start_time
        print(f"\r{self.desc} is complete in {run_time}", end="")


def progressbar(func):
    def wrapper(*args, **kwargs):
        progress_bar = ProgressBarPrinter(desc=func.__name__)
        process = func(*args, **kwargs)
        while True:
            try:
                progress = next(process)
                progress_bar.update(progress)
            except StopIteration as result:
                progress_bar.end_bar()
                return result.value

    return wrapper


@progressbar
def dummy_loop(n_iter):
    n_iter = n_iter
    for i in range(n_iter):
        time.sleep(0.1)
        yield (i + 1) / n_iter
    return "ALL DONE"


def main():
    result = dummy_loop(17)
    print(f"\n{result}")


if __name__ == "__main__":
    main()
