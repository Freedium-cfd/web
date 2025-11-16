import requests

server_url = input(
    "Enter your Freedium instance server URL (for example: http://localhost:6752/ ): "
)

# List of some problematic Medium posts
url_for_test = {
    "https://medium.com/@godfreythegreat/stop-wasting-your-life-27832c8f6644",
    "https://medium.com/@iamalexmathers/21-sentences-that-will-make-you-more-attractive-than-most-b4ee755ee6c5?source=explore---------0-83--------------------9b9b2ec7_ee6e_4cfb_bb69_db1451bfb3db-------15",
    "https://levelup.gitconnected.com/some-linux-commands-that-can-boost-your-work-efficiency-dramatically-9dc802a10618",
    "https://leshchuk.medium.com/http-cache-on-rails-nginx-stack-950fee2f8eef",
    "https://medium.com/swlh/35-actionable-tips-to-grow-your-medium-blog-4e4017b89905",
    "https://valeman.medium.com/benchmarking-neural-prophet-part-i-neural-prophet-vs-prophet-252990763468",  # Stil have a problems
    "https://valeman.medium.com/python-vs-r-for-time-series-forecasting-395390432598",
    "https://medium.com/@aleb/how-to-generate-random-user-agents-with-an-api-22aad3d232cb",
    "https://medium.com/angular-in-depth/the-best-way-to-unsubscribe-rxjs-observable-in-the-angular-applications-d8f9aa42f6a0",
    "515dd5a43948",  # full address: https://medium.com/macoclock/12-macos-apps-so-good-you-will-wonder-how-they-are-free-515dd5a43948
    "https://anudeep-vysyaraju.medium.com/how-any-gitamite-can-get-free-linkedin-premium-membership-d4222bd1a0b3",  # <--- Check for non properly aligned emojies
    "https://johndanielraines.medium.com/be-an-engineer-not-a-frameworker-c58fe28d0c88",
    "https://medium.com/coding-beauty/parseint-strange-behavior-cdff5e1f9ff7",  # <---- Title renderer some weird characters
    "https://medium.com/macoclock/the-11-craziest-and-most-advanced-macos-tips-tricks-ive-ever-seen-cd842ce3f0a3",  # Still have some problem on paragraph_id 236e7049b537_43
    "https://www.freedium.cfd/c81e00f6320d",
}

blacklist_url = {"51e23c5a2aac", "e65e737baa29", "70e83061e535"}


def main():
    for url in url_for_test:
        print(f"Processing: {url}")
        request = requests.get(server_url + url)
        if request.status_code != 200:
            raise ValueError(f"Can't process URL: {url}")


if __name__ == "__main__":
    main()
