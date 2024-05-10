import { Link, Outlet, json, useLoaderData, useParams } from "@remix-run/react";
import { client } from "~/client";
import { ActivityCard } from "~/components/ActivityCard";

interface Activity {
  type: string;
  source: string;
  occurred_at: Date;
}

export const loader = async () => {
  const downloads = await client.GET("/api/downloads", {
    params: {
      query: {
        _start: 0,
        _end: 10,
        _order: "DESC",
        _sort: "downloaded_at",
      },
    },
  });

  if (!downloads.data) return;

  const assets = await Promise.all(
    downloads.data.map(({ asset_id }) =>
      client.GET("/api/assets/{id}", { params: { path: { id: asset_id } } }),
    ),
  );

  if (!assets.every(Boolean)) return;

  return json({
    downloads: downloads.data,
    assets: assets.map((a) => a.data),
  });
};

interface MyActivityCardProps {
  d: { asset_id: number; source: string; downloaded_at: string };
}

function MyActivityCard({ d }: MyActivityCardProps) {
  const { assets } = useLoaderData<typeof loader>();
  const asset = assets.find(({ id }) => id === d.asset_id);
  const { id } = useParams();

  if (!asset) return null;

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
  const { downloads } = useLoaderData<typeof loader>();
  return (
    <div className="flex h-full flex-col gap-2 p-4">
      <input placeholder="Search" className="mr-6 rounded-xl border p-2" />

      <div className="flex h-full flex-row flex-wrap content-start gap-4 overflow-auto p-4">
        {downloads.map((d) => (
          <MyActivityCard d={{ source: "cults3d", ...d }} />
        ))}
      </div>

      <Outlet />
    </div>
  );
}
