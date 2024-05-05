import { json, useLoaderData } from "@remix-run/react";
import { ClipboardCopy } from "lucide-react";
import { client } from "~/client";
import { CultsLogo, MmfLogo } from "~/components/icons";

interface Activity {
  type: string;
  source: string;
  occurred_at: Date;
}

export const loader = async () => {
  const res = client.GET("/api/mmf/status");
  const res2 = client.GET("/api/cults/status");
  return json({ mmf: (await res).data, cults: (await res2).data });
};

function CopyChip({ data }: { data: any }) {
  return (
    <div className="flex flex-row items-center gap-1 self-start rounded-full border backdrop-hue-rotate-90">
      <div className="py-1 pl-3 font-mono">{data}</div>
      <div
        className="cursor-pointer rounded-e-full pr-1 hover:backdrop-hue-rotate-90"
        onClick={() => navigator.clipboard.writeText(`${data}`)}
      >
        <ClipboardCopy className="py-0.5" preserveAspectRatio="yes" />
      </div>
    </div>
  );
}

function MmfStatus() {
  const { mmf } = useLoaderData<typeof loader>();

  return (
    <div className="flex flex-col gap-4 self-start rounded-lg border border-emerald-200 bg-emerald-100 p-2">
      <div className="flex flex-row items-center gap-1">
        <MmfLogo />
        <h1 className="text-xl">MMF Status</h1>
      </div>

      {!mmf ? (
        <p>No data</p>
      ) : (
        <>
          <div className="flex flex-col">
            <p>UserId</p>
            <CopyChip data={mmf.user_id} />
          </div>

          <div className="flex flex-col">
            <p>
              AccessToken - Expires At{" "}
              {new Date(mmf.access_exp).toLocaleString()}
            </p>
            <CopyChip data={mmf.access_token} />
          </div>

          <div className="flex flex-col">
            <p>
              RefreshToken - Expires At{" "}
              {new Date(mmf.refresh_exp).toLocaleString()}
            </p>
            <CopyChip data={mmf.refresh_token} />
          </div>
        </>
      )}
    </div>
  );
}

function CultsStatus() {
  const { cults } = useLoaderData<typeof loader>();
  return (
    <div className="flex flex-col gap-4 self-start rounded-lg  border border-purple-200 bg-purple-100 p-2">
      <div className="flex flex-row items-center gap-1">
        <CultsLogo />
        <h1 className="text-xl">Cults Status</h1>
      </div>

      {!cults ? (
        <p>No data</p>
      ) : (
        <div className="flex flex-col">
          <p>Email</p>
          <CopyChip data={cults?.email} />
        </div>
      )}
    </div>
  );
}

export default function Activity() {
  return (
    <div className="flex flex-col gap-4">
      <MmfStatus />
      <CultsStatus />
    </div>
  );
}
