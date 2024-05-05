import { json, useLoaderData } from "@remix-run/react";
import { client } from "~/client";

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

const CultsLogo = (
  <img
    className="h-12 w-12 rounded-full"
    src="/cults3d.png"
    alt="Cults3d Logo"
  />
);

const MmfLogo = (
  <img
    className="h-12 w-12 rounded-full"
    src="/mmf.jpg"
    alt="MyMiniFactory Logo"
  />
);

function ActivityCard({
  d,
}: {
  d: { asset_id: number; source: string; downloaded_at: string };
}) {
  const { assets } = useLoaderData<typeof loader>();
  const asset = assets.find(({ id }) => id === d.asset_id);

  return (
    <div className="flex rounded-xl bg-white p-6 shadow-lg border gap-4">
      <img
        src={asset?.illustration_url}
        className="h-32 w-32 rounded-full bg-purple-500"
      />
      <div>
        <div className="flex flex-row items-center text-xl font-medium gap-4  text-black">
          <div className="shrink-0">
            {d.source === "cults3d" ? CultsLogo : MmfLogo}
          </div>
          Download
        </div>

        <p className="text-slate-400">
          {new Date(d.downloaded_at).toLocaleString()}
        </p>

        <p className="text-slate-400">{asset?.name}</p>
      </div>
    </div>
  );
}

export default function Activity() {
  const { downloads } = useLoaderData<typeof loader>();
  return (
    <div className="flex h-full flex-row flex-wrap content-start gap-2 overflow-auto p-4">
      {downloads.map((d) => (
        <ActivityCard d={{ source: "cults3d", ...d }} />
      ))}
    </div>
  );
}
