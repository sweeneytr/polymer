"use client"; // only needed if you choose App Router
import { Admin, Resource, ListGuesser, EditGuesser } from "react-admin";
import jsonServerProvider from "ra-data-json-server";

const dataProvider = jsonServerProvider("http://localhost:8000");

const AdminApp = () => (
  <Admin dataProvider={dataProvider}>
    <Resource
      name="assets"
      list={ListGuesser}
      recordRepresentation="name"
    />
  </Admin>
);

export default AdminApp;