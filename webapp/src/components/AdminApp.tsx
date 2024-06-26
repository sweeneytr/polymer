"use client"; // only needed if you choose App Router
import {
  Admin,
  Resource,
  BooleanInput,
  UrlField,
  SearchInput,
  Button,
  useRecordContext,
  DateField,
  ImageField,
  ReferenceArrayField,
  SimpleShowLayout,
  Show,
  ReferenceManyField,
  SingleFieldList,
  ChipField,
  ReferenceField,
  Pagination,
  ReferenceManyCount,
  Create,
  SimpleForm,
  TextInput,
  ReferenceInput,
  DataProvider,
} from "react-admin";
import jsonServerProvider from "ra-data-json-server";
import {
  BooleanField,
  Datagrid,
  List,
  NumberField,
  TextField,
} from "react-admin";
import PlayCircleFilledIcon from "@mui/icons-material/PlayCircleFilled";
import get from "lodash/get";
import axios from "axios";
import DownloadForOfflineIcon from "@mui/icons-material/DownloadForOffline";
import React, { useEffect, useState } from "react";
import { QueryClient } from "react-query";

const assetFilters = [
  <SearchInput source="q" alwaysOn />,
  <BooleanInput source="yanked" />,
  <BooleanInput source="downloaded" />,
  <BooleanInput source="free" />,
];
export const AssetList = () => (
  <List filters={assetFilters}>
    <Datagrid rowClick="show">
      <TextField source="id" />
      <ImageField source="illustration_url" label="Illustration" />
      <TextField source="slug" />
      <TextField source="name" />
      <TextField source="details" />
      <TextField source="description" />
      <ReferenceField source="creator_id" reference="users" link="show" />
      <NumberField
        source="cents"
        label="Cost"
        options={{
          style: "currency",
          currency: "USD",
          minimumFractionDigits: 2,
        }}
        transform={(x) => x / 100}
      />
      <BooleanField source="yanked" />
      <ReferenceArrayField reference="tags" source="tag_ids">
        <SingleFieldList linkType="show">
          <ChipField source="label" />
        </SingleFieldList>
      </ReferenceArrayField>
      <UrlButton source="nab_url" label="Download" method="redirect">
        <DownloadForOfflineIcon />
      </UrlButton>
    </Datagrid>
  </List>
);

export const AssetShow = () => (
  <Show>
    <SimpleShowLayout>
      <TextField source="id" />
      <ImageField source="illustration_url" />
      <ImageField source="illustrations" src="src" />
      <TextField source="slug" />
      <TextField source="name" />
      <TextField source="details" />
      <TextField source="description" />
      <ReferenceField source="creator_id" reference="users" link="show" />
      <NumberField
        source="cents"
        label="Cost"
        options={{
          style: "currency",
          currency: "USD",
          minimumFractionDigits: 2,
        }}
        transform={(x) => x / 100}
      />
      <BooleanField source="yanked" />
      <ReferenceArrayField reference="tags" source="tag_ids">
        <SingleFieldList linkType="show">
          <ChipField source="label" />
        </SingleFieldList>
      </ReferenceArrayField>
      <UrlButton source="nab_url" label="Download" method="redirect">
        <DownloadForOfflineIcon />
      </UrlButton>
      <ReferenceArrayField reference="downloads" label="Downloads" source="download_ids">
        <Datagrid rowClick="show">
          <ChipField source='id'/>
          <TextField source="filename" />
        </Datagrid>
      </ReferenceArrayField>
    </SimpleShowLayout>
  </Show>
);

const tagFilters = [<SearchInput source="q" alwaysOn />];
export const TagList = () => (
  <List filters={tagFilters}>
    <Datagrid rowClick="show">
      <TextField source="id" />
      <TextField source="label" />
      <ReferenceManyCount label="Assets" reference="assets" target="tag_id" />
    </Datagrid>
  </List>
);

export const TagShow = () => (
  <Show>
    <SimpleShowLayout>
      <TextField source="id" />
      <TextField source="label" />
      <ReferenceManyField
        label="Assets"
        reference="assets"
        target="tag_id"
        pagination={<Pagination />}
      >
        <Datagrid rowClick="show">
          <TextField source="slug" />
          <ImageField source="illustration_url" label="Illustration" />
          <ReferenceField source="creator_id" reference="users" link="show" />
          <ReferenceArrayField reference="tags" source="tag_ids">
            <SingleFieldList linkType="show">
              <ChipField source="label" />
            </SingleFieldList>
          </ReferenceArrayField>
          <NumberField
            source="cents"
            label="Cost"
            options={{
              style: "currency",
              currency: "USD",
              minimumFractionDigits: 2,
            }}
            transform={(x) => x / 100}
          />
          <UrlButton source="nab_url" label="Download" method="redirect">
            <DownloadForOfflineIcon />
          </UrlButton>
        </Datagrid>
      </ReferenceManyField>
    </SimpleShowLayout>
  </Show>
);

const userFilters = [<SearchInput source="q" alwaysOn />];
export const UserList = () => (
  <List filters={userFilters}>
    <Datagrid rowClick="show">
      <TextField source="id" />
      <TextField source="nickname" />
      <ReferenceManyCount
        label="Assets"
        reference="assets"
        target="creator_id"
      />
    </Datagrid>
  </List>
);

export const UserShow = () => (
  <Show>
    <SimpleShowLayout>
      <TextField source="id" />
      <TextField source="nickname" />

      <ReferenceArrayField
        reference="assets"
        source="asset_ids"
        pagination={<Pagination />}
      >
        <Datagrid rowClick="show">
          <TextField source="slug" />
          <ImageField source="illustration_url" label="Illustration" />
          <ReferenceArrayField reference="tags" source="tag_ids">
            <SingleFieldList linkType="show">
              <ChipField source="label" />
            </SingleFieldList>
          </ReferenceArrayField>
          <NumberField
            source="cents"
            label="Cost"
            options={{
              style: "currency",
              currency: "USD",
              minimumFractionDigits: 2,
            }}
            transform={(x) => x / 100}
          />
          <UrlButton source="nab_url" label="Download" method="redirect">
            <DownloadForOfflineIcon />
          </UrlButton>
        </Datagrid>
      </ReferenceArrayField>
    </SimpleShowLayout>
  </Show>
);

const taskFilters = [<SearchInput source="q" alwaysOn />];
export const TaskList = () => (
  <List filters={taskFilters}>
    <Datagrid rowClick="edit">
      <TextField source="name" />
      <TextField source="cron" />
      <BooleanField source="startup" />
      <DateField source="last_run_at" showTime />
      <NumberField source="last_duration" />
      <UrlButton source="run_url" label="Run" method="post">
        <PlayCircleFilledIcon />
      </UrlButton>
    </Datagrid>
  </List>
);

const categoryFilters = [<SearchInput source="q" alwaysOn />];
export const CategoryList = () => (
  <List filters={categoryFilters}>
    <Datagrid rowClick="show">
      <TextField source="id" />
      <TextField source="label" />
    </Datagrid>
  </List>
);

export const CategoryShow = () => (
  <Show>
    <SimpleShowLayout>
      <TextField source="id" />
      <ReferenceField reference="categories" source="parent_id" link="show"/>
      <ReferenceArrayField reference="categories" source="child_ids">
        
      <SingleFieldList linkType="show">
              <ChipField source="label" />
            </SingleFieldList>
            </ReferenceArrayField>
      <TextField source="label" />
    </SimpleShowLayout>
  </Show>
);

export const CategoryCreate = () => (
  <Create >
    <SimpleForm>
      <ReferenceInput reference="categories" source="parent_id" />
      <TextInput source="label" />
    </SimpleForm>
  </Create>
);

const downloadFilters = [<SearchInput source="q" alwaysOn />];
export const DownloadList = () => (
  <List filters={downloadFilters}>
    <Datagrid rowClick="show">
      <TextField source="id" />
      <ReferenceField reference="assets" source="asset_id" link="show" />
      <TextField source="filename" />
      <DateField showTime source="downloaded_at" />
    </Datagrid>
  </List>
);

export const DownloadShow = () => (
  <Show>
    <SimpleShowLayout>
      <TextField source="id" />
      <ReferenceField reference="assets" source="asset_id" link="show" />
      <TextField source="filename" />
      <DateField showTime source="downloadedAt" />
    </SimpleShowLayout>
  </Show>
);


const UrlButton = ({
  source,
  method,
  ...rest
}: {
  source: string;
  method: "get" | "post" | "redirect";
  [key: string]: any;
}) => {
  const record = useRecordContext();
  const url = record ? get(record, source) : null;

  const handleClick = () => {
    switch (method) {
      case "redirect":
        window.location = url;
        break;
      case "get":
        axios.get(url);
        break;
      case "post":
        axios.post(url);
        break;
    }
  };
  return url ? <Button onClick={handleClick} {...rest} /> : null;
};

const AdminApp = () => {
  const [dataProvider, setDataProvider] = useState<DataProvider | undefined>(undefined);
  
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 5 * 60 * 1000, // 5 minutes
      },
    },
  });
  
  useEffect(() => {
    setDataProvider(jsonServerProvider(`http://127.0.0.1:8000/api`))
  }, []);

  return (
    <Admin dataProvider={dataProvider} queryClient={queryClient}>
      <Resource
        name="assets"
        list={AssetList}
        show={AssetShow}
        recordRepresentation="name"
      />
      <Resource
        name="downloads"
        list={DownloadList}
        show={DownloadShow}
        recordRepresentation="id"
      />
      <Resource
        name="tags"
        list={TagList}
        show={TagShow}
        recordRepresentation="label"
      />
      <Resource name="tasks" list={TaskList} recordRepresentation="name" />
      <Resource
        name="users"
        list={UserList}
        show={UserShow}
        recordRepresentation="nickname"
      />
      <Resource
        name="categories"
        list={CategoryList}
        create={CategoryCreate}
        show={CategoryShow}
        recordRepresentation="label"
      />
    </Admin>
  );
};

export default AdminApp;
