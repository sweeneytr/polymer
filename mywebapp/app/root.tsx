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
  useMatches,
} from "@remix-run/react";
import stylesheet from "~/tailwind.css";
import { Upload } from "lucide-react";

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

function Header() {
  return (
    <header className="flex flex-row items-center border-b-2 bg-slate-100">
      <img src="/favicon.png" className="m-2 h-12 w-12" />
      <h1 className="text-2xl">Polymer</h1>

      <div className="ml-auto" />
      <Upload className="m-2" />
      <input placeholder="Search" className="mr-6 rounded-xl p-2" />
    </header>
  );
}

function SideNav() {
  const matches = useMatches();
  const pathnames = matches.map(({ pathname }) => pathname);

  return (
    <nav className="w-60 border-r-2 bg-slate-100 p-4">
      <ul>
        <li>
          <Link
            to="/"
            className={pathnames[1] === "/" ? "text-blue-500" : undefined}
          >
            Home
          </Link>
        </li>
        <li>
          <Link
            to="/activity"
            className={
              pathnames[1] === "/activity" ? "text-blue-500" : undefined
            }
          >
            Activity
          </Link>
        </li>
        <li>
          <Link
            to="/models"
            className={
              pathnames[1] === "/models" ? "text-blue-500" : undefined
            }
          >
            Models
          </Link>
        </li>
      </ul>
    </nav>
  );
}

function Footer() {
  return (
    <footer className="flex justify-end bg-black p-2 pr-6 text-white">
      <span>© Tristan Sweeney, 2024</span>
    </footer>
  );
}

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
        <Header />
        <div className="flex flex-1 flex-row">
          <SideNav />
          <div className="flex-1 p-4">
            <Outlet />
          </div>
        </div>
        <Footer />
        <ScrollRestoration />
        <Scripts />
        <LiveReload />
      </body>
    </html>
  );
}
