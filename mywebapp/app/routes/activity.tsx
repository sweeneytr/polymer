import {
  Link,
  Outlet,
  json,
  useFetcher,
  useLoaderData,
  useParams,
  useSearchParams,
} from "@remix-run/react";
import { useCallback, useEffect, useState } from "react";
import { client } from "~/client";
import { ActivityCard } from "~/components/ActivityCard";
import { components } from "../api";
import { LoaderFunction, LoaderFunctionArgs } from "@remix-run/node";
import { InfiniteScroller } from "~/components/InfiniteScroll";

interface Activity {
  type: string;
  source: string;
  occurred_at: Date;
}

export const loader = async ({ request }: LoaderFunctionArgs) => {
  const page = parseInt(new URL(request.url).searchParams.get("page") ?? "1");
  const n = page - 1;
  const N = 10;

  const downloads = await client.GET("/api/downloads", {
    params: {
      query: {
        _start: n * N,
        _end: page * N,
        _order: "DESC",
        _sort: "downloaded_at",
      },
    },
  });

  if (!downloads.data) {
    throw new Error("Error fetching downloads");
  }

  console.log("fetched downloads")
  console.log(downloads.data.length);

  const assets = await Promise.all(
    downloads.data.map(({ asset_id }) =>
      client.GET("/api/assets/{id}", { params: { path: { id: asset_id } } }),
    ),
  );

  if (!assets.every(Boolean)) {
    throw new Error("Could not fetch all assets");
  }

  return json({
    data: {
      downloads: downloads.data,
      assets: assets.map((a) => a.data),
    },
    page,
  });
};

interface MyActivityCardProps {
  d: { asset_id: number; source: string; downloaded_at: string };
  asset: components["schemas"]["AssetModel"];
}

function MyActivityCard({ d, asset }: MyActivityCardProps) {
  const { id } = useParams();

  return (
    <Link className={"cursor-pointer"} to={`./${d.asset_id}`}>
      <ActivityCard
        source={d.source}
        downloadedAt={new Date(d.downloaded_at)}
        url={asset.illustration_url ?? undefined}
        title={asset.name}
        creator={asset.creator}
        focused={!!id && asset.id === parseInt(id)}
      />
    </Link>
  );
}

export default function Activity() {
  const loaded = useLoaderData<typeof loader>();
  const fetcher = useFetcher<typeof loader>();
  const [page, setPage] = useState(loaded.page);
  const [{ downloads, assets }, setItems] = useState(loaded.data);

  useEffect(() => {
    if (!fetcher.data || fetcher.state === "loading") {
      return;
    }
    // If we have new data - append it
    if (fetcher.data) {
      const { downloads: newDownloads, assets: newAssets } = fetcher.data.data;
      setItems(({ downloads, assets }) => ({
        downloads: [...downloads, ...newDownloads],
        assets: [...assets, ...newAssets],
      }));
    }
  }, [fetcher.data]);

  const loadNext = useCallback(() => {
    const page = fetcher.data ? fetcher.data.page + 1 : loaded.page + 1;
    const query = `?index&page=${page}`;
    fetcher.load(query); // this call will trigger the loader with a new query
  }, [fetcher, loaded]);

  const [searchParams, setSearchParams] = useSearchParams();
  return (
    <div className="flex h-full flex-col gap-2 p-4">
      <input
        placeholder="Search"
        className="mr-6 rounded-xl border p-2"
        value={searchParams.get("search") ?? ""}
        onChange={(e) => {
          setSearchParams({ search: e.currentTarget.value });
        }}
      />

      <InfiniteScroller
        loadNext={loadNext}
        loading={fetcher.state === "loading"}
      >
        <div className="flex h-full flex-row flex-wrap content-start gap-4 overflow-auto p-4">
          {downloads.map((d) => {
            const asset = assets.find(({ id }) => id === d.asset_id);
            if (!asset) return null;

            return (
              <MyActivityCard d={{ source: "cults3d", ...d }} asset={asset} />
            );
          })}
        </div>
      </InfiniteScroller>

      <Outlet />
    </div>
  );
}
