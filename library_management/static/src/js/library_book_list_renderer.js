/** @odoo-module **/

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListRenderer } from "@web/views/list/list_renderer";
import { ListController } from "@web/views/list/list_controller";
import { Component, onMounted, onPatched, onWillUnmount, useState, xml } from "@odoo/owl";

// Tooltip Component
class DescriptionTooltip extends Component {
    static template = xml`
        <div class="book-tooltip p-2 bg-light border shadow-sm"
             t-att-style="state.style">
            <t t-esc="state.description"/>
        </div>
    `;
    
    setup() {
        this.state = useState({ 
            style: "display: none;",
            description: "" 
        });
        
        // Expose API to parent component
        this.props.registerAPI({
            showAt: (x, y, description) => this.showAt(x, y, description),
            hide: () => this.hide()
        });
    }

    showAt(x, y, description) {
    const tooltipWidth = 300;
    if (x + tooltipWidth > window.innerWidth) {
    x = window.innerWidth - tooltipWidth - 10;
    }
    this.state.description = description;
    this.state.style = `
        display: block; 
        position: fixed; 
        top: ${y}px; 
        left: ${x}px; 
        z-index: 9999; 
        pointer-events: none;
        max-width: 300px;
    `;

    // Add the 'visible' class

    }

    hide() {
        this.state.style = "display: none;";
    }
}

// Custom Renderer
class LibraryBookListRenderer extends ListRenderer {
    static template = xml`
        <div>
            <t t-call="web.ListRenderer"/>
            <DescriptionTooltip 
                t-if="state.tooltipMounted"
                registerAPI="registerTooltipAPI"
            />
        </div>
    `;
    
    static components = { 
        ...ListRenderer.components,
        DescriptionTooltip 
    };

    setup() {
        super.setup();
        this.tooltipAPI = null;
        this.state = useState({ tooltipMounted: false });
        
        onMounted(() => {
            this.state.tooltipMounted = true;
            this.setupEventDelegation();
        });
        
        onPatched(() => this.setupEventDelegation());
        onWillUnmount(() => this.cleanup());
    }

    registerTooltipAPI = (api) => {
        this.tooltipAPI = api;
    };

    setupEventDelegation() {
        const table = this.tableRef?.el;
        if (!table) return;
        
        // Clean up previous listeners
        table.removeEventListener('mouseover', this.onMouseOver);
        table.removeEventListener('mouseout', this.onMouseOut);
        
        // Create new bound handlers
        this.onMouseOver = this.handleMouseOver.bind(this);
        this.onMouseOut = this.handleMouseOut.bind(this);
        
        // Add new listeners
        table.addEventListener('mouseover', this.onMouseOver);
        table.addEventListener('mouseout', this.onMouseOut);
    }

    handleMouseOver(event) {
        if (!this.tooltipAPI) return;
        
        const row = event.target.closest('tr[data-id]');
        if (!row) return;

        const id = row.getAttribute('data-id');
        const record = this.props.list.records.find(r => r.id.toString() === id);
        const description = record?.data?.description;
        if (!description) return;

        const rect = row.getBoundingClientRect();
        const scrollY = window.scrollY || window.pageYOffset;
        this.tooltipAPI.showAt(rect.left, rect.bottom + scrollY + 5, description);
    }

    handleMouseOut(event) {
        if (!this.tooltipAPI) return;
        
        const row = event.target.closest('tr[data-id]');
        if (row) {
            this.tooltipAPI.hide();
        }
    }

    cleanup() {
        const table = this.tableRef?.el;
        if (table) {
            table.removeEventListener('mouseover', this.onMouseOver);
            table.removeEventListener('mouseout', this.onMouseOut);
        }
        this.tooltipAPI = null;
    }
}

// Controller
class LibraryBookListController extends ListController {}

// View Definition
const LibraryBookListView = {
    ...listView,
    Renderer: LibraryBookListRenderer,
    Controller: LibraryBookListController,
    fields: ["name", "description"],
};

registry.category("views").add("library_book_list", LibraryBookListView);