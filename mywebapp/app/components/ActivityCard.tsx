import classNames from "classnames";
import { CultsLogo, MmfLogo } from "./icons";

interface Props {
  focused?: boolean;
  source: string;
  url?: string;
  creator: string;
  downloadedAt: Date;
  title: string;
}

function Image({ url }: { url?: string }) {
  return (
    <div className="m-2 h-32 w-32 overflow-hidden rounded-xl border bg-purple-500 shadow-sm">
      {url && (
        <img src={url} alt="Asset Illustration" className="h-full w-full" />
      )}
    </div>
  );
}

export function ActivityCard({ focused, source, url, title, creator, downloadedAt}: Props) {
  return (
    <div
      className={classNames(
        "flex gap-4 overflow-hidden rounded-2xl border-2",
        "bg-white shadow-lg hover:border-purple-300 hover:shadow-purple-400",
        { "border-purple-300 shadow-purple-400": focused },
      )}
    >
    <Image url={url} />
      <div className="py-4 pr-4">
        <div className="flex flex-row items-center gap-4 ">
          <span className="max-w-xs text-xl text-black">{title}</span>
        </div>

        <div className="flex flex-row items-center gap-4">
            {source === "cults3d" ? <CultsLogo /> : <MmfLogo />}

          <div className="flex flex-col">
            <p className="text-slate-400">{creator}</p>
            <p className="text-slate-400">
              {downloadedAt.toLocaleString()}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
