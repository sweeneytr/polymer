import { json, useLoaderData } from "@remix-run/react";
import { client } from "~/client";
import { CultsLogo, MmfLogo } from "~/components/icons";

interface Activity {
  type: string;
  source: string;
  occurred_at: Date;
}

export const loader = async () => {
  const res = client.GET("/api/mmf/status");
  return json((await res).data);
};

export default function Activity() {
  const data = useLoaderData<typeof loader>();
  return (
    <div className="flex flex-col gap-4">
      <div>
        <div className="flex flex-row items-center gap-1">
          <MmfLogo />
          <h1 className="text-xl">MMF Status</h1>
        </div>
        <p>UserId</p>
        <p>{data.user_id}</p>
        <p>AccessToken - Expires At {new Date(data.access_exp).toLocaleString()}</p>
        <p>{data.access_token}</p>
        <p>RefreshToken - {new Date(data.refresh_exp).toLocaleString()}</p>
        <p>{data.refresh_token}</p>
      </div>
      <div>
        <div className="flex flex-row items-center gap-1">
          <CultsLogo />
          <h1 className="text-xl">Cults Status</h1>
        </div>
      </div>
    </div>
  );
}
