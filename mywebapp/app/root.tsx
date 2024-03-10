import { cssBundleHref } from "@remix-run/css-bundle";
import type { LinksFunction } from "@remix-run/node";
import {
  Link,
  Links,
  LiveReload,
  Meta,
  Outlet,
  Scripts,
  ScrollRestoration,
} from "@remix-run/react";
import stylesheet from "~/tailwind.css";

export const links: LinksFunction = () => [
  ...(cssBundleHref
    ? [
        { rel: "stylesheet", href: cssBundleHref },
        {
          rel: "icon",
          href: "/favicon.png",
          type: "image/png",
        },
        { rel: "stylesheet", href: stylesheet },
      ]
    : [
        {
          rel: "icon",
          href: "/favicon.png",
          type: "image/png",
        },
        { rel: "stylesheet", href: stylesheet },
      ]),
];

export default function App() {
  return (
    <html lang="en" className="h-full">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <Meta />
        <Links />
      </head>
      <body className="flex h-full w-full flex-col">
        <header className="flex flex-row items-center border-b-2 bg-slate-100">
          <img src="/favicon.png" className="m-2 h-12 w-12" />
          <h1 className="text-2xl">Polymer</h1>

          <input placeholder="Search" className="ml-auto p-2 rounded-xl mr-6" />
        </header>
        <div className="flex flex-1 flex-row">
          <nav className="w-60 border-r-2 bg-slate-100 pl-4 pt-4">
            <ul>
              <li>
                <Link to="/" className="text-blue-500">Home</Link>
              </li>
              <li>
                <Link to="/activity">Activity</Link>
              </li>
            </ul>
          </nav>
          <div className="flex-1 p-4">
            <Outlet />
          </div>
        </div>
        <footer className="flex justify-end bg-black p-2 pr-6 text-white">
          <span>© Tristan Sweeney, 2024</span>
        </footer>
        <ScrollRestoration />
        <Scripts />
        <LiveReload />
      </body>
    </html>
  );
}
