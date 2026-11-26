# Not another neural style implementation!

Recreate photos in in the style of famous artists with machine learning.
CSCI3341 Artificial Intelligence Final Project.

## Usage

The model installer needs `curl` and GNU coreutils. Obtain an independently verified SHA-256 digest for the [Oxford VGG-19 Caffe weights](https://www.robots.ox.ac.uk/~vgg/research/very_deep/), then run from the project directory.

    VGG19_SHA256='replace-with-verified-sha256' sh util/download_models.sh

The published model metadata does not include a SHA-256 digest. The installer requires one before it will download any weights and only installs a matching file.

    python art.py --help

## Examples

Create a (low quality) version of the image below. The first positional
argument is the content image and the image(s) after are the style
images. The further options instruct the algorithm to run for 200 iterations
and output an image with a 256px maximum width, which should be doable
relatively quickly on a personal computer.

    python art.py examples/gasson.jpg examples/starry.jpg -n 200 -w 256

Further options include using the entire oeuvre of an artist as a stylistic
target (which never works well), scaling the stylistic features by a factor,
specifying whether to initialize the candidate image from random noise or the
content image, and more. See the script's help for details.

The best [Gassongram](https://www.instagram.com/explore/tags/gassongram/) ever:

![gasson](https://raw.githubusercontent.com/jayelm/neural-art/master/examples/gasson.jpg)
![starry](https://raw.githubusercontent.com/jayelm/neural-art/master/examples/starry.jpg)
![gasson_final](https://raw.githubusercontent.com/jayelm/neural-art/master/examples/gasson_final.jpg)

## Where do I get all this art?

Set `ARTISTS` in `util/wikiart-scraper.py` to the WikiArt slugs you want to fetch, such as `pablo-picasso`. The optional fetcher uses Python 3.9 or later.

    python3 util/wikiart-scraper.py

The script saves up to 100 JPEGs per artist from the links embedded in the public gallery page, under `wikiart/<artist>/`.
