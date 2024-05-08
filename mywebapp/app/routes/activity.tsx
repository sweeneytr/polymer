import { Link, Outlet, json, useLoaderData, useParams } from "@remix-run/react";
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
  const {id} = useParams();
  

  let className = "flex cursor-pointer gap-4 overflow-hidden rounded-2xl border-2 bg-white shadow-lg hover:border-purple-300 hover:shadow-purple-400";
  if (id && d.asset_id === parseInt(id)) {
    className += " border-purple-300 shadow-purple-400"
  }

  return (
    <Link
      className={className}
      to={`./${d.asset_id}`}
    >
      <div className="h-32 w-32 overflow-hidden rounded-r-full border bg-purple-500">
        {asset?.illustration_url ? (
          <img
            src={asset.illustration_url}
            alt="Asset Illustration"
            className="h-full w-full"
          />
        ) : (
          <></>
        )}
      </div>
      <div className="py-4 pr-4">
        <div className="flex flex-row items-center gap-4 text-xl font-medium  text-black">
          <div className="shrink-0">
            {d.source === "cults3d" ? CultsLogo : MmfLogo}
          </div>{asset?.name}
        </div>

        <p className="text-slate-400">{asset?.creator}</p>
        <p className="text-slate-400">
          {new Date(d.downloaded_at).toLocaleString()}
        </p>

      </div>
    </Link>
  );
}

export default function Activity() {
  const { downloads } = useLoaderData<typeof loader>();
  return (
    <div className="flex h-full flex-row flex-wrap content-start gap-2 overflow-auto p-4">
      <Outlet />
      {downloads.map((d) => (
        <ActivityCard d={{ source: "cults3d", ...d }} />
      ))}
    </div>
  );
}
