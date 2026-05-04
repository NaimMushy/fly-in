import time


def animate_dots(
    string: str,
    loop_count: int,
) -> None:

    print(end=string)

    for _ in range(loop_count):

        for _ in range(3):

            print(end='.', flush=True)
            time.sleep(0.5)

        print(end='\b\b\b', flush=True)
        print(end='   ', flush=True)
        print(end='\b\b\b', flush=True)

    print("\n")
