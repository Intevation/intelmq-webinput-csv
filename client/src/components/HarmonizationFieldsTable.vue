<template>
  <div>
    <b-table
      sticky-header="600px"
      ref="table"
      striped
      bordered
      small
      :fields="tableHeader"
      :items="rowsOnShownPage"
    >
      <template #head(-1)="">
        Ac&shy;tions
      </template>
      <template #head()="data">
        <div style="resize: horizontal; overflow-x: auto;">
          <harmonization-field-select
            :value="internalFieldAssignments[data.column]"
            @update="update(data.column, $event)"
          />
          <div v-if="columnValidityErrors[data.column]" style="color: red;">{{ columnValidityErrors[data.column] }}</div>
          <div v-if="isColumnMultipleFieldAssignment[data.column]" style="color: orange;">Multiple field assignment!</div>
        </div>
      </template>
      <template #cell(-1)="data">
        <div
          :class="getTableRowClass(paginationOffset + data.index)"
          style="display: flex; flex-direction: row; flex-wrap: wrap; justify-content: center; align-items: center; row-gap: 2px; font-variant-numeric: tabular-nums;"
        >
          <div
            v-b-tooltip.hover
            :title="getTableRowTooltip(paginationOffset + data.index)"
            style="padding: 0 2px;"
          >#{{ paginationOffset + data.index + 1 }}</div>
          <div
            style="padding: 0 2px;"
          ><b-button
            size="sm"
            @click="showRowModal(data.item)"
            variant="info"
          >🔎</b-button></div>
        </div>
      </template>
      <template #cell()="data">
        <div
          :class="getTableCellClass(paginationOffset + data.index, data.field.key)"
        ><span
          v-b-tooltip.hover
          :title="getTableCellTooltip(paginationOffset + data.index, data.field.key)"
          style="overflow-wrap: break-word;"
        >{{ data.value }}</span></div>
      </template>
    </b-table>
    <b-container>
      <b-row>
        <b-col>
          <b-form-group
            label="Per page"
            label-for="per-page-select"
            label-cols="6"
            label-size="sm"
            class="mb-0"
          >
            <b-form-select
              id="per-page-select"
              v-model="perPage"
              :options="[5, 10, 25, 100]"
              size="sm"
            />
          </b-form-group>
        </b-col>
        <b-col>
          <b-pagination
            v-model="currentPage"
            :total-rows="dataRows.length"
            :per-page="perPage"
            align="fill"
            size="sm"
            class="my-0"
          />
        </b-col>
      </b-row>
    </b-container>
    <b-modal
      ref="rowModal"
      title="Processed Row Data"
      scrollable
      size="xl"
      ok-only
      @hidden="rowModalData = null, rowModalError = null, rowModalOwner = null"
    >
      <div v-show="!(rowModalData || rowModalError)">Waiting for response from server…</div>
      <div v-show="rowModalError">
        <h5>Got error:</h5>
        <pre><code>{{ rowModalError }}</code></pre>
      </div>
      <div v-show="rowModalData">
        <div v-show="rowModalDataNotifications.length">
          <h5>Notifications ({{ rowModalDataNotifications.length }}):</h5>
          <b-container v-for="notification in rowModalDataNotifications" v-bind:key="notification.index">
            <h6>Subject: {{ notification[0] }}</h6>
            <h6>To: {{ notification[1] }}</h6>
            <h6>Content Type: {{ notification[3] }}</h6>
            <pre><code>{{ notification[2] }}</code></pre>
          </b-container>
        </div>
        <div v-show="!rowModalDataNotifications.length">
          <h5>No notifications</h5>
        </div>
        <div v-show="rowModalDataMessages.length">
          <h5>Messages ({{ rowModalDataMessages.length }}) after processing by bots (excluding output bots):</h5>
          <pre><code>{{ rowModalDataMessages }}</code></pre>
        </div>
        <div v-show="!rowModalDataMessages.length">
          <h5>No messages</h5>
        </div>
        <div v-show="rowModalDataLog">
          <h5>Log:</h5>
          <pre><code>{{ rowModalDataLog }}</code></pre>
        </div>
        <div v-show="!rowModalDataLog">
          <h5>Nothing logged</h5>
        </div>
      </div>
    </b-modal>
  </div>
</template>

<script>
// Documentation on b-table:
// https://github.com/bootstrap-vue/bootstrap-vue/blob/dev/src/components/table/README.md

import harmonizationFieldSelect from './HarmonizationFieldSelect.vue';
import { parseMIME } from '../util/parseMIME.js';

export default ({
  name: 'HarmonizationFieldsTable',
  props: {
    fieldAssignments: {
      type: Array,
      default: () => []
    },
    dataRows: {
      type: Array,
      default: () => []
    },
    dataErrors: {
      type: [Object, Array],
      default: () => ({})
    },
    errorFieldAssignments: {
      // The state of fieldAssignments when dataErrors was generated
      type: Array,
      default: () => []
    },
    getRowPromise: {
      type: Function,
      default: () => (/*row*/) => new Promise((res, rej) => {rej({body: 'getRowPromise not provided to HarmonizationFieldsTable component'});})
    },
    getFieldNameValidationPromise: {
      type: Function
    }
  },
  components: {harmonizationFieldSelect},
  data() {
    return {
      internalFieldAssignmentsStr: JSON.stringify(this.fieldAssignments),
      fieldNameValidationErrors: {},
      rowModalData: null,
      rowModalError: null,
      rowModalOwner: null,
      currentPage: 1,
      perPage: 25
    };
  },
  computed: {
    internalFieldAssignments() {
      return JSON.parse(this.internalFieldAssignmentsStr);
    },
    tableHeader() {
      const count = this.internalFieldAssignments.length + 1;
      const headerArray = Array(count);
      for (let i = 0; i < count; ++i) {
        headerArray[i] = {key: String(i - 1)};
      }
      return headerArray;
    },
    paginationOffset() {
      return ((this.currentPage || 1) - 1) * this.perPage;
    },
    rowsOnShownPage() {
      return this.dataRows.slice(this.paginationOffset, this.paginationOffset + this.perPage);
    },
    isColumnMultipleFieldAssignment() {
      const f = this.internalFieldAssignments;
      return f.map((cur, i) => cur && f.some((el, j) => j !== i && el === cur));
    },
    columnValidityErrors() {
      return this.internalFieldAssignments.map(name => this.fieldNameValidationErrors[name]);
    },
    rowModalDataNotifications() {
      return (this.rowModalData || {}).notifications || [];
    },
    rowModalDataMessages() {
      return (this.rowModalData || {}).messages || [];
    },
    rowModalDataLog() {
      return (this.rowModalData || {}).log || '';
    }
  },
  watch: {
    dataRows() {
      this.currentPage = 1;
    },
    fieldAssignments(newFieldAssignments) {
      // If the assigned string is the same, this will not cause reactive updates
      this.internalFieldAssignmentsStr = JSON.stringify(newFieldAssignments);
      const knownFields = Object.keys(this.fieldNameValidationErrors);
      const getter = this.getFieldNameValidationPromise;
      for (const field of newFieldAssignments) {
        if (!field) continue;
        if (knownFields.includes(field)) {
          const fieldError = this.fieldNameValidationErrors[field];
          if (fieldError === null || fieldError === 'Invalid field name') continue;
        }
        if (!getter) {
          this.$set(this.fieldNameValidationErrors, field, 'Failed to check field name validity (missing getFieldNameValidationPromise prop)');
          continue;
        }
        getter(field).then(response => {
          if (response.status === 200) {
            response.json().then(responseJson => {
              if (responseJson.status === undefined) {
                this.$set(this.fieldNameValidationErrors, field, 'Failed to check field name validity (missing status field in response JSON)');
              } else if (!responseJson.status) {
                this.$set(this.fieldNameValidationErrors, field, 'Invalid field name');
              } else {
                this.$set(this.fieldNameValidationErrors, field, null); // No error, is valid
              }
            }, (/*parseError*/) => {
              this.$set(this.fieldNameValidationErrors, field, 'Failed to check field name validity (bad JSON in response)');
            });
          } else {
            this.$set(this.fieldNameValidationErrors, field, 'Failed to check field name validity (got status code ' + response.status + ' from server)');
          }
        }, (/*error*/) => {
          this.$set(this.fieldNameValidationErrors, field, 'Failed to check field name validity (HTTP or network error)');
        });
      }
    }
  },
  methods: {
    showRowModal(row) {
      const myself = {}; // Unique object
      this.rowModalData = null;
      this.rowModalError = null;
      this.rowModalOwner = myself;
      this.getRowPromise(row).then(successResponse => {
        successResponse.json().then(data => {
          if (this.rowModalOwner !== myself) return;
          if (data.notifications) data.notifications = data.notifications.map(parseMIME);
          this.rowModalData = data;
          this.rowModalError = null;
        }, error => {
          if (this.rowModalOwner !== myself) return;
          this.rowModalData = null;
          this.rowModalError = 'Could not parse response body as JSON, ' + (error ? 'error: ' + error : 'no details available');
        });
      }, errorResponse => {
        if (this.rowModalOwner !== myself) return;
        this.rowModalData = null;
        this.rowModalError = 'POST request failed, ' + (errorResponse.body ? 'got response: ' + errorResponse.body : 'no reason given (empty response body)');
      });
      this.$refs.rowModal.show();
    },
    update(column, value) {
      this.$emit('updateField', {column, value});
    },
    getTableRowClass(row) {
      return this.getTableRowTooltip(row) ? 'table-danger' : '';
    },
    getTableRowTooltip(row) {
      return ((this.dataErrors[row] || {})[-1] || []).join(' • ');
    },
    getTableCellClass(row, col) {
      return this.getTableCellTooltip(row, col) ? 'table-danger' : this.dataErrors[row] ? 'table-warning' : '';
    },
    getTableCellTooltip(row, col) {
      return ((this.dataErrors[row] || {})[this.errorFieldAssignments[col]] || []).join(' • ');
    }
  }
})
</script>
