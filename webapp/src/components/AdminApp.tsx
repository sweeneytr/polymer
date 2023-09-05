"use client"; // only needed if you choose App Router
import { Admin, Resource, ListGuesser, EditGuesser, BooleanInput, UrlField, SearchInput, Button, useRecordContext, DateField } from "react-admin";
import jsonServerProvider from "ra-data-json-server";
import { BooleanField, Datagrid, List, NumberField, TextField } from 'react-admin';
import get from 'lodash/get';
import axios from 'axios';

const dataProvider = jsonServerProvider("http://localhost:8000");

const assetFilters = [
  <SearchInput source="q" alwaysOn />,
  <BooleanInput source="yanked" />,
  <BooleanInput source="downloaded" />,
  <BooleanInput source="free" />,
];
export const AssetList = () => (
    <List filters={assetFilters}>
        <Datagrid rowClick="edit">
            <TextField source="id" />
            <TextField source="slug" />
            <TextField source="name" />
            <TextField source="details" />
            <TextField source="description" />
            <TextField source="creator" />
            <NumberField source="cents" />
            <UrlField source="download_url" />
            <BooleanField source="yanked" />
            <BooleanField source="downloaded" />
            <BooleanField source="free" />
            <UrlField source="nab_url" sortable={false} />
        </Datagrid>
    </List>
);

const tagFilters = [
  <SearchInput source="q" alwaysOn />
];
export const TagList = () => (
  <List filters={tagFilters}>
      <Datagrid rowClick="edit">
          <TextField source="id" />
          <TextField source="label" />
      </Datagrid>
  </List>
);

const taskFilters = [
  <SearchInput source="q" alwaysOn />
];
export const TaskList = () => (
  <List filters={taskFilters}>
      <Datagrid rowClick="edit">
          <TextField source="name" />
          <TextField source="cron" />
          <BooleanField source="startup" />
          <DateField source="last_run_at" showTime />
          <NumberField source="last_duration" />
          <UrlButton source="run_url" label="Run now" />
      </Datagrid>
  </List>
);

const UrlButton = ({ source, ...rest }: {source: string}) => {
  const record = useRecordContext();
  const handleClick = () => {
    axios.post(get(record, source));
  }
  return record ? <Button onClick={handleClick} {...rest} /> : null;
}

const AdminApp = () => (
  <Admin dataProvider={dataProvider}>
    <Resource
      name="assets"
      list={AssetList}
      recordRepresentation="name"
    />
    <Resource
      name="tags"
      list={TagList}
      recordRepresentation="label"
    />
    <Resource
      name="tasks"
      list={TaskList}
      recordRepresentation="name"
    />
  </Admin>
);

export default AdminApp;