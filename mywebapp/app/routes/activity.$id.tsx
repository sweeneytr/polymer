import { Dialog } from "@headlessui/react";
import { client } from "~/client";
import { LoaderFunctionArgs, json } from "@remix-run/node";
import invariant from "tiny-invariant";
import { useLoaderData, useNavigate } from "@remix-run/react";
import { CultsLogo } from "~/components/icons";
import { Download } from "lucide-react";

export const loader = async ({ params: { id } }: LoaderFunctionArgs) => {
  invariant(id, "Missing path param `id`");
  const asset = await client.GET("/api/assets/{id}", {
    params: { path: { id: parseInt(id) } },
  });

  if (!asset.data) return;

  const downloads = Promise.all(
    asset.data.download_ids.map((id) =>
      client.GET("/api/downloads/{id}", { params: { path: { id } } }),
    ),
  );

  return json({
    asset: asset.data,
    downloads: (await downloads).map((d) => d.data),
  });
};

export default function Page() {
  const navigate = useNavigate();
  const {
    asset: {
      name,
      description,
      creator,
      illustration_url,
      yanked,
      download_ids,
    },
    downloads,
  } = useLoaderData<typeof loader>();

  return (
    <Dialog
      open={true}
      onClose={() => {
        navigate(-1);
      }}
    >
      <div className="fixed inset-0 bg-black/25" aria-hidden="true" />

      <div className="fixed inset-0 flex items-center justify-center">
        <Dialog.Panel className="max-w-3xl rounded-2xl bg-white p-6 shadow-xl overflow-y-auto max-h-2xl justify-center flex flex-col gap-4">
          <div className="flex flex-row items-center gap-2">
            <img src={illustration_url} className="h-40 rounded-xl border shadow-sm" />
            <div className="flex flex-col">
              <Dialog.Title className="text-2xl">{name}</Dialog.Title>
              <div className="flex flex-row items-center gap-2">
                <CultsLogo />
                <div className="flex flex-col">
                  <span>{creator}</span>
                  <span className="text-gray-400">
                    {yanked ? "Yanked from Cults" : "Still on Cults"}
                  </span>
                </div>
              </div>
            </div>
          </div>
          <Dialog.Description>{description}</Dialog.Description>

          <hr className="h-0.5 bg-neutral-100 dark:bg-white/10" />

          <table className="border-separate border-spacing-x-4 self-center">
            <thead>
                <tr>
                    <th>Version</th>
                    <th>Downloaded At</th>
                </tr>
            </thead>
            <tbody>
              {downloads.map(({ downloaded_at, id }, idx) => (
                <tr>
                    <td>{idx + 1}</td>
                  <td>{new Date(downloaded_at).toLocaleString()}</td>
                  <td><a href={`http://localhost:8000/api/downloads/${id}/download`} className="hover:text-blue-500"><Download/></a></td>
                </tr>
              ))}
            </tbody>
          </table>
        </Dialog.Panel>
      </div>
    </Dialog>
  );
}
