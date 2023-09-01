class Grave:
    async def _find_username(self) -> str:
        html = await self.get_parsed("https://cults3d.com/en/profile/edit")
        return html.find("input", {"name": "users_profile[nick]"})["value"]

    async def _create_api_key(self) -> str:
        html = await self.get_parsed("https://cults3d.com/en/api/keys")

        res_html = await self.post_parsed(
            "https://cults3d.com/en/api/keys",
            html=html,
            data={"commit": "Create+API+Key"},
            follow_redirects=True,
        )

        return (
            res_html.find(id="new-api-key")
            .find("span", {"data-copy-target": "text"})
            .text.strip()
        )

    async def _delete_api_key(self, api_key: str) -> None:
        html = await self.get_parsed("https://cults3d.com/en/api/keys")

        for key in html.findAll("tr", id=lambda x: x and x.startswith("api_key_")):
            key_prefix = key.find("code").text.strip().rstrip("*")

            if api_key.startswith(key_prefix):
                href = key.find("a", {"data-method": "delete"})["href"]
                await self.post_parsed(
                    f"https://cults3d.com{href}", html=html, data={"_method": "delete"}
                )
                break
        else:
            # couldn't find api key?
            pass

    @asynccontextmanager
    async def _with_api_key(self) -> collections.abc.AsyncIterator[str]:
        try:
            key = await self._create_api_key()
            yield key
        finally:
            await self._delete_api_key(key)
