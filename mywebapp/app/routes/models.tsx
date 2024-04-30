import { json, useLoaderData } from "@remix-run/react";
import { CultsLogo, MmfLogo } from "~/components/icons";

interface Activity {
  type: string;
  source: string;
  occurred_at: Date;
}

export const loader = async () => {
  return json([
    { type: "download", source: "cults3d", occurred_at: new Date() },
    { type: "download", source: "cults3d", occurred_at: new Date() },
  ]);
};

function ActivityCard({d}: {d: {source: string, occurred_at: string, type: string}}) {
    return <div className="mx-auto flex max-w-sm items-center space-x-4 rounded-xl bg-white p-6 shadow-lg">
          <div className="shrink-0">
            {d.source === "cults3d" ? <CultsLogo /> : <MmfLogo />}
          </div>
          <div>
            <div className="text-xl font-medium text-black">{d.type}</div>
            <p className="text-slate-400">{d.type} - {new Date(d.occurred_at).toLocaleString()}</p>
          </div>
        </div>
}

export default function Activity() {
  const data = useLoaderData<typeof loader>();
  return (
    <div>
      {data.map((d) => <ActivityCard d={d}/>)}
    </div>
  );
}
