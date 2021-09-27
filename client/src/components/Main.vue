<template>
  <div>
    <b-navbar toggleable="lg" type="dark" variant="info">
      <b-navbar-brand href="#">IntelMQ - Webinput CSV</b-navbar-brand>
      <b-navbar-nav v-if="hasAuth" class="ml-auto">
        <b-button v-if="!loggedIn" v-b-modal.login-popup size="sm" class="my-2 my-sm-0" type="submit">Login</b-button>
        <b-button v-if="loggedIn" size="sm" class="my-2 my-sm-0" @click="signOut">Logout</b-button>
      </b-navbar-nav>
    </b-navbar>
    <div>
      <b-modal v-model="showLogin" id="login-popup" title="IntelMQ - Webinput-CSV - Sign in">
        <label v-if="wrongCredentials" class="text-danger">Wrong username or password</label>
        <b-form>
          <div>
            <label for="username">Username</label>
            <b-form-input v-model="username" type="text" id="username"  placeholder="Name"></b-form-input>
            <label for="password">Password</label>
            <b-form-input v-model="password" type="password" id="password"  placeholder="Password"></b-form-input>
          </div>
        </b-form>
        <template #modal-footer>
            <b-button
              variant="primary"
              size="sm"
              class="float-right"
              @click="signIn"
            >
              Login
            </b-button>
        </template>   
      </b-modal>
    </div>
    <div v-if="loggedIn">
      <div class="accordion" role="tablist">
        <b-card no-body class="mb-1">
          <b-card-header header-tag="header" class="p-1" role="tab">
            <b-button block v-b-toggle.accordion-1 variant="info">CSV Content</b-button>
          </b-card-header>
          <b-collapse id="accordion-1" visible accordion="my-accordion" role="tabpanel">
            <b-card-body>
              <b-container fluid>
                <b-row>
                  <b-col cols="11">
                    <b-form-group >
                      <b-form-file
                        v-model="csvFile"
                        placeholder="Choose a file or drop it here..."
                        drop-placeholder="Drop file here..."
                        @input="readFromFile"
                      ></b-form-file>
                    </b-form-group>
                  </b-col>
                  <b-col>
                    <b-button @click="reset">Clear</b-button>
                  </b-col>
                </b-row>
              </b-container>
              <b-container fluid>
                <b-form-group >
                  <b-form-textarea
                    v-if="!csvFile"
                    id="textarea"
                    v-model="csvText"
                    placeholder="Or paste CSV data here"
                    rows="5"
                    @change="parseCSV"
                  ></b-form-textarea>
                  <b-form-textarea
                    v-if="!!csvFile"
                    id="textareaPreview"
                    v-model="csvPreviewText"
                    rows="5"
                  ></b-form-textarea>
                </b-form-group>
              </b-container>
              <b-container fluid>
                <b-row>
                  <b-col>
                    <b-form-group label-cols=7 label="Delimiter">
                      <b-form-select
                        v-model="delimiter"
                        :options="delimiterOptions"
                        @change="parseCSV"
                      ></b-form-select>
                    </b-form-group>
                  </b-col>
                  <b-col>
                    <b-form-group label-cols=7 label="Quote char">
                      <b-form-input
                        v-model="quoteChar"
                        type="text"
                        placeholder='"'
                        @change="parseCSV"
                      ></b-form-input>
                    </b-form-group>
                  </b-col>
                  <b-col>
                    <b-form-group label-cols=7 label="Escape char">
                      <b-form-input
                        v-model="escapeChar"
                        type="text"
                        placeholder="\"
                        @change="parseCSV"
                      ></b-form-input>
                    </b-form-group>
                  </b-col>
                  <b-col>
                    <b-form-group label-cols=7 label="Has Header">
                      <b-form-checkbox
                        v-model="hasHeader"
                        @change="parseCSV"
                      ></b-form-checkbox>
                    </b-form-group>
                  </b-col>
                  <b-col>
                    <b-form-group id="option1" label-cols=9 label="Skip initial Whitespace">
                      <b-form-checkbox
                        v-model="initialWhitespace"
                        @change="parseCSV"
                      ></b-form-checkbox>
                    </b-form-group>
                    <b-tooltip target="option1" triggers="hover">
                      When True, whitespace immediately following the delimiter is ignored.
                    </b-tooltip>
                  </b-col>
                  <b-col>
                    <b-form-group id="option2" label-cols=7 label="Skip initial N lines">
                      <b-form-input
                        v-model="skipLines"
                        type="number"
                        @change="parseCSV"
                      ></b-form-input>
                    </b-form-group>
                    <b-tooltip target="option2" triggers="hover">
                      Skip initial N lines after the header.
                    </b-tooltip>
                  </b-col>
                </b-row>
              </b-container>
            </b-card-body>
          </b-collapse>
        </b-card>

        <b-card no-body class="mb-1">
          <b-card-header header-tag="header" class="p-1" role="tab">
            <b-button :disabled="!csvFile && csvText === ''" block v-b-toggle.accordion-3 variant="info">Preview</b-button>
          </b-card-header>
          <b-collapse id="accordion-3" accordion="my-accordion" role="tabpanel">
            <b-card-body>
              <b-container fluid>
                <b-row>
                  <b-col>
                    <label>Lines: {{ lines }}, Errors: {{ errors }} </label>
                    <b-form-group label-cols=4 label="Timezone">
                      <b-form-select
                        v-model="timezone"
                        :options="timezones"
                      ></b-form-select>
                    </b-form-group>
                    <b-form-group label-cols=4 label="Dryrun">
                      <b-form-checkbox
                        v-model="dryrun"
                      ></b-form-checkbox>
                    </b-form-group>
                    <b-container>
                      <b-row>
                        <b-col>
                          <b-button @click="sendData">Send data</b-button>
                        </b-col>
                        <b-col>
                          <label style="margin-left: 10px;" :class="transferStatus">{{ transfered }}</label>
                        </b-col>
                      </b-row>
                    </b-container>
                  </b-col>
                  <b-col>
                    <label>Constant fields(fallback)</label>
                    <b-form-group label-cols=4 label="classification type">
                      <b-form-select
                        v-model="classificationType"
                        :options="classificationTypes"
                      ></b-form-select>
                    </b-form-group>
                    <b-form-group v-for="field in customFieldsMapping" :key="field.key" :id="field.key" label-cols=4 :label="field.key">
                      <b-form-input v-model="field.value" type="text"></b-form-input>
                    </b-form-group>
                  </b-col>
                </b-row>
              </b-container>
              <b-table sticky-header="600px"
                ref="table"
                striped
                bordered
                :current-page="currentPage"
                :per-page="perPage"
                :fields="tableHeader"
                :items="tableData"
              >
                <template #head()="data">
                  <span class="text-info">{{ data.label }}</span>
                  <b-form-select
                    :id="data.label"
                    v-model="data.field.field"
                    :options="harmonizationFields"
                    @change="update(data)"
                  ></b-form-select>
                  <b-tooltip :target="data.label" triggers="hover">
                    {{ data.field.field }}
                  </b-tooltip>
                  <b-form-checkbox
                    v-model="data.field.selected"
                    @change="update(data)"
                  ></b-form-checkbox>
                </template>
                <template #foot(name)="data">
                  <span class="text-danger">{{ data.label }}</span>
                </template>
                <template #foot()="data">
                  <i>{{ data.label }}</i>
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
                        :options="pageOptions"
                        size="sm"
                      ></b-form-select>
                    </b-form-group>
                  </b-col>
                  <b-col>
                    <b-pagination
                      v-model="currentPage"
                      :total-rows="lines"
                      :per-page="perPage"
                      align="fill"
                      size="sm"
                      class="my-0"
                    ></b-pagination>
                  </b-col>
                </b-row>
              </b-container>
            </b-card-body>
          </b-collapse>
        </b-card>
      </div>
    </div>
  </div>
</template>

<script>
import { mapState } from 'vuex';
import parse from 'papaparse';
export default ({
  data: () => {
    return {
      username: "",
      password: "",
      showLogin: false,
      wrongCredentials: false,
      csvFile: null,
      csvText: "",
      csvPreviewText: "",
      csvData: [],
      delimiter: ";",
      delimiterOptions: [
        {value: ";", text: ";"},
        {value: ",", text: ","},
        {value: "#", text: "#"}
      ],
      quoteChar: '"',
      escapeChar: "\\",
      hasHeader: false,
      initialWhitespace: false,
      skipLines: 0,
      parserResult: {},
      lines: 0,
      errors: 0,
      timezones: [],
      timezone: '+00:00',
      dryrun: true,
      classificationType: "blacklist",
      identifier: "test",
      code: "oneshot",
      tableHeader: [],
      tableData: [],
      currentPage: 1,
      pageOptions: [5, 10, 25, 100],
      perPage: 25,
      totalRows: 1,
      transfered: "",
      transferStatus: "text-danger"
    }
  },
  computed: {
    ...mapState(['user', 'loggedIn', 'hasAuth', 'classificationTypes', 'harmonizationFields', 'customFieldsMapping']),
  },
  mounted() {
    // Create timezone strings
    for (var i = -12; i <= 12; i++) {
      var timeZoneString = '';
      if (i < 0) {
          if ((i / -10) < 1) {
              timeZoneString = '-0' + (-i);
              this.timezones.push(timeZoneString);
          } else {
              this.timezones.push(i.toString());
          }
      } else {
          if ((i / 10) < 1) {
              timeZoneString = '+0' + i;
              this.timezones.push(timeZoneString);
          } else {
              this.timezones.push('+' + i.toString());
          }
      }
    }
    for (var j = 0; j < this.timezones.length; j++) {
        this.timezones[j] = this.timezones[j] + ':00';
    }
  },
  methods: {
    /**
     * Prepare and aggregate data and send the post request.
     */
    sendData: function() {
      let data = []
      for (let item of this.parserResult.data) {
        let sendItem = {};
        for (let ndx in this.tableHeader) {
          // check for header in csv. data is array or object
          if (this.tableHeader[ndx].selected
            && this.tableHeader[ndx].field !== ""
          ) {
            let value;
            if (this.hasHeader) {
              value = item[this.tableHeader[ndx].key]
            } else {
              value = item[ndx];
            }
            sendItem[this.tableHeader[ndx].field] = this.prepare(this.tableHeader[ndx].field, value)
          }
        }
        data.push(sendItem);
      }
      let custom = {
          "custom_classification.type": this.classificationType,
      };
      for (let field of this.customFieldsMapping) {
        custom["custom_"+field.key] = field.value;
      }
      let send = {
        timezone: this.timezone,
        data: data,
        custom: custom,
        dryrun: this.dryrun
      }
      var me = this;
      this.$http.post('api/upload', send)
        .then(response => {
          if (response.status !== 200) {
            me.trasferStatus = "text-danger";
            me.transfered = "Send failed!";
            return;
          }
          response.json().then(data => {
            me.transfered = "Injected " + (data.total - data.lines_invalid) + " lines. " + data.lines_invalid + " were invalid."
            me.transferStatus = "text-black"
          })
        });
    },
    /**
     * Function to preprocess values.
     */
    prepare: function(field, value) {
      if (field === "extra") {
        try {
          value = JSON.parse(value)
        }
        catch(e) {
          return {data: value};
        }
        if (Array.isArray(value)) {
          return {data: value};
        }
      }
      return value;
    },
    reset: function() {
      this.csvFile = null;
      this.csvText = "";
    },
    /**
     * Update the table header and refresh view.
     */
    update: function(value) {
      let ndx = this.tableHeader.findIndex(item => {
        if (item.key === value.column) {
          return true;
        }
      })
      this.tableHeader[ndx] = value.field;
      this.$refs.table.refresh();
    },
    /**
     * Trigger login.
     */
    signIn: function () {
      this.$store.dispatch("login", {
        username: this.username,
        password: this.password
      }).then(() => {
        this.wrongCredentials = false
        this.$bvModal.hide("login-popup")
        this.$store.dispatch("fetchClassificationTypes");
        this.$store.dispatch("fetchHarmonizationFields");
        this.$store.dispatch("fetchCustomFields");
      }, () => {
          this.wrongCredentials = true
      })
    },
    /**
     * Trigger logout.
     */
    signOut: function () {
      this.username = ''
      this.password = ''
      this.wrongCredentials = false
      this.$store.dispatch("logout")
    },
    /**
     * Read the uploaded csv file and trigger parsing the content.
     */
    readFromFile() {
      if (!this.csvFile) {
        this.csvText = "";
        this.parseCSV();
      }
      const me = this;
      return new Promise((resolve) => {
        if (this.csvFile) {
          var reader = new FileReader();
          reader.onload = function(event) {
            me.csvText = event.target.result;
            me.csvPreviewText = event.target.result.substring(0, 2000) + "\n\u2026";
            me.parseCSV();
            resolve();
          };
          reader.readAsText(this.csvFile);
        }
      });
    },
    /**
     * Parse the csv data and apply user options.
     */
    parseCSV() {
      // Option to trim whitespaces.
      if (this.initialWhitespace) {
        var regEx = "\\s*" + this.delimiter + "\\s*";
        var re = new RegExp(regEx,"g");
        this.csvText = this.csvText.replace(re, this.delimiter);
      }
      let count = 0;
      const me = this;
      this.parserResult.data = [];
      this.parserResult.errors = [];
      parse.parse(this.csvText, {
        delimiter: this.delimiter,
        quoteChar: this.quoteChar,
        escapeChar: this.escapeChar,
        header: this.hasHeader,
        skipEmptyLines: true,
        step: function(row) {
          if (me.skipLines > 0 && count < me.skipLines) {
            count++
            return;
          }
          me.parserResult.data.push(row.data);
          me.parserResult.errors.concat(row.errors);
          me.parserResult.meta = row.meta;
          return;
        }
      });
      if (this.parserResult.meta.aborted) {
        return;
      }
      if (this.parserResult.data.length === 0) {
        return;
      }
      this.lines = this.parserResult.data.length;
      this.errors = this.parserResult.errors.length;
      let columns;
      if (this.hasHeader
        && this.parserResult.meta.fields
      ) {
        columns = this.parserResult.meta.fields.map(function(i) {
          return {
            key: i,
            label: i
          }
        });
      } else  {
        columns = Array.apply(null, { length: this.parserResult.data[0].length }).map(function(i, ndx) {
          return {
            key: ""+ndx,
            label: "column-"+ndx
          }
        });
      }
      this.tableHeader.length = 0;
      for (let i in columns) {
        this.tableHeader.push({
          key: columns[i].key,
          label: columns[i].label,
          selected: false,
          field: ""
        })

      }
      this.tableData = this.parserResult.data;
    }
  }
})
</script>
