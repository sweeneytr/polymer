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

const dataProvider = jsonServerProvider("http://localhost:8000");

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
      <ImageField source="illustration_url" />
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
      <UrlField source="download_url" />
      <BooleanField source="yanked" />
      <BooleanField source="downloaded" />
      <BooleanField source="free" />
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
      <UrlField source="download_url" />
      <BooleanField source="yanked" />
      <BooleanField source="downloaded" />
      <BooleanField source="free" />
      <ReferenceArrayField reference="tags" source="tag_ids">
        <SingleFieldList linkType="show">
          <ChipField source="label" />
        </SingleFieldList>
      </ReferenceArrayField>
      <UrlButton source="nab_url" label="Download" method="redirect">
        <DownloadForOfflineIcon />
      </UrlButton>
    </SimpleShowLayout>
  </Show>
);

const tagFilters = [<SearchInput source="q" alwaysOn />];
export const TagList = () => (
  <List filters={tagFilters}>
    <Datagrid rowClick="show">
      <TextField source="id" />
      <TextField source="label" />
    </Datagrid>
  </List>
);

export const TagShow = () => (
  <Show>
    <SimpleShowLayout>
      <TextField source="id" />
      <TextField source="label" />
      <ReferenceManyField label="Assets" reference="assets" target="tag_id">
        <Datagrid rowClick="show">
          <TextField source="slug" />
          <ReferenceArrayField reference="tags" source="tag_ids">
            <SingleFieldList linkType="show">
              <ChipField source="label" />
            </SingleFieldList>
          </ReferenceArrayField>
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
    </Datagrid>
  </List>
);

export const UserShow = () => (
  <Show>
    <SimpleShowLayout>
      <TextField source="id" />
      <TextField source="nickname" />

      <ReferenceArrayField reference="assets" source="asset_ids">
        <Datagrid rowClick="show">
          <TextField source="slug" />
          <ReferenceArrayField reference="tags" source="tag_ids">
            <SingleFieldList linkType="show">
              <ChipField source="label" />
            </SingleFieldList>
          </ReferenceArrayField>
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

const UrlButton = ({
  source,
  method,
  ...rest
}: {
  source: string;
  method: "get" | "post" | "redirect";
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

const AdminApp = () => (
  <Admin dataProvider={dataProvider}>
    <Resource
      name="assets"
      list={AssetList}
      show={AssetShow}
      recordRepresentation="name"
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
  </Admin>
);

export default AdminApp;
